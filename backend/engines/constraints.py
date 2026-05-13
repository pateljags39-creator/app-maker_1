"""Bounded-customization constraints registry.

A Constraints object scopes what the AI may change on a project. It is consumed by
the Improve workflow (engines/improve_engine.py) and by the Repair workflow
(engines/repair_engine.py). Hard rules (no .env edits, no secrets, no escapes from
workspace) are always enforced regardless of the user's per-project settings.

Design goals:
* Defaults are SENSIBLE for a typical generated React+Vite + FastAPI app.
* Validation runs OFFLINE (no LLM) and is fully deterministic.
* Single function `validate_change(...)` is the only entry point both engines use.
* Honest violations: every rejected change explains WHY in plain English.
"""
from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

# Path parts that the AI may NEVER touch (hard rule). These are not user-tunable.
HARD_FORBIDDEN_PARTS: set[str] = {
    ".env", ".env.local", ".env.production",
    ".factory", "node_modules", "dist", "build", ".git",
}

# Filename patterns (any part of the relative path) considered secrets containers.
HARD_FORBIDDEN_GLOBS: tuple[str, ...] = (
    "*credentials*.json", "*.pem", "*.key", "*token.json*",
)

# Patterns that look like leaked keys / secrets in file content. Used to reject
# any change that would write a recognisable secret into the workspace.
_SECRET_REGEXES: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}\b"),         # google api keys
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),              # openai-ish
    re.compile(r"\bsk-emergent-[A-Za-z0-9]{12,}\b"),     # emergent llm key
    re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |)PRIVATE KEY-----"),
    re.compile(r"\bxoxb-[A-Za-z0-9-]{20,}\b"),           # slack bot tokens
)


@dataclass
class ProjectConstraints:
    """User-tunable bounds on what the AI may change.

    Hard rules (forbidden paths, no-secrets, no-writes-outside-workspace) are
    enforced separately by `validate_change` regardless of these values.
    """

    # ---- Change budget ----
    max_files_changed: int = 8         # total replace+create+delete operations
    max_new_files: int = 5             # new files created in a single change
    max_total_loc_changed: int = 1500  # rough budget on lines touched

    # ---- Scope ----
    # Subset of {"frontend", "backend", "root"}. "root" allows top-level files
    # like README.md / .gitignore. Defaults allow everything inside workspace.
    allowed_areas: list[str] = field(default_factory=lambda: ["frontend", "backend", "root"])
    no_new_top_level_dirs: bool = True

    # ---- Dependencies ----
    allow_npm_deps_changes: bool = True
    allow_pip_deps_changes: bool = True
    max_new_npm_deps: int = 5
    max_new_pip_deps: int = 5

    # ---- Meta ----
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any] | None) -> "ProjectConstraints":
        d = dict(d or {})
        defaults = cls()
        # Only known keys win, others ignored; type-coerce ints/bools.
        for k, v in list(d.items()):
            if not hasattr(defaults, k):
                d.pop(k, None)
        # Coerce types so JSON payloads with strings still work.
        for k in ("max_files_changed", "max_new_files", "max_total_loc_changed",
                  "max_new_npm_deps", "max_new_pip_deps"):
            if k in d:
                try:
                    d[k] = int(d[k])
                except Exception:
                    d[k] = getattr(defaults, k)
        for k in ("no_new_top_level_dirs", "allow_npm_deps_changes", "allow_pip_deps_changes"):
            if k in d:
                d[k] = bool(d[k])
        if "allowed_areas" in d:
            aa = d["allowed_areas"]
            if isinstance(aa, str):
                aa = [a.strip() for a in aa.split(",") if a.strip()]
            d["allowed_areas"] = [a for a in (aa or []) if a in {"frontend", "backend", "root"}]
            if not d["allowed_areas"]:
                d["allowed_areas"] = defaults.allowed_areas
        return cls(**d)


def default_constraints() -> dict[str, Any]:
    """Return the canonical defaults as a plain dict (safe to store in Mongo)."""
    return ProjectConstraints().to_dict()


# ---------- Validation ----------

def _is_secret_content(text: str) -> str | None:
    """Return the matched secret excerpt if `text` looks like it contains a
    real credential. Returns None otherwise."""
    sample = text[:200_000]  # cap scanning cost
    for rx in _SECRET_REGEXES:
        m = rx.search(sample)
        if m:
            return m.group(0)[:24] + "…"
    return None


def _is_path_forbidden(rel_path: str) -> str | None:
    """Return reason if path violates hard rules, else None."""
    if not rel_path or rel_path.startswith("/"):
        return "absolute path not allowed"
    parts = Path(rel_path).parts
    if ".." in parts:
        return "parent-directory escapes not allowed"
    pset = set(parts)
    bad = pset & HARD_FORBIDDEN_PARTS
    if bad:
        return f"path touches forbidden segment: {sorted(bad)[0]}"
    for glob in HARD_FORBIDDEN_GLOBS:
        if any(fnmatch.fnmatch(p, glob) for p in parts):
            return f"path matches forbidden glob: {glob}"
    return None


def _area_of(rel_path: str) -> str:
    """Bucket a relative path into 'frontend' | 'backend' | 'root'."""
    parts = Path(rel_path).parts
    if not parts:
        return "root"
    head = parts[0]
    if head == "frontend":
        return "frontend"
    if head == "backend":
        return "backend"
    return "root"


def _normalize_action(action: str | None) -> str:
    a = (action or "replace").strip().lower()
    if a in {"replace", "update", "edit", "overwrite"}:
        return "replace"
    if a in {"create", "add", "new"}:
        return "create"
    if a in {"delete", "remove", "rm"}:
        return "delete"
    return a  # unknown -> caller will reject


def _existing_top_level_dirs(workspace: Path) -> set[str]:
    if not workspace.exists():
        return set()
    return {p.name for p in workspace.iterdir() if p.is_dir() and p.name not in HARD_FORBIDDEN_PARTS}


def validate_change(
    workspace: Path,
    manifest: dict[str, Any],
    constraints: dict[str, Any] | None = None,
) -> tuple[bool, list[str], dict[str, Any]]:
    """Validate an LLM-produced change manifest against project constraints.

    Returns:
        (ok, violations, summary_stats)

    `summary_stats` is always populated (counts) so the caller can persist it
    even on reject.

    Manifest schema (consumed):
        {
          "summary": str,
          "rationale": str,
          "files": [
            {"path": str, "action": "replace"|"create"|"delete", "new_content": str?}
          ],
          "add_npm_deps": [{"name": str, "version": str}],
          "add_pip_deps": [str]
        }
    """
    c = ProjectConstraints.from_dict(constraints or {})
    violations: list[str] = []
    files = manifest.get("files") or []
    if not isinstance(files, list):
        violations.append("manifest.files must be a list")
        files = []

    workspace = Path(workspace)
    existing_top = _existing_top_level_dirs(workspace)

    n_total = 0
    n_new = 0
    n_loc = 0
    seen_paths: set[str] = set()

    for i, entry in enumerate(files):
        if not isinstance(entry, dict):
            violations.append(f"files[{i}] is not an object")
            continue
        path = (entry.get("path") or "").strip()
        action = _normalize_action(entry.get("action"))
        content = entry.get("new_content") or ""

        if not path:
            violations.append(f"files[{i}].path is required")
            continue
        if path in seen_paths:
            violations.append(f"files[{i}] duplicates earlier path: {path}")
        seen_paths.add(path)

        # Hard rule: forbidden paths.
        fb = _is_path_forbidden(path)
        if fb is not None:
            violations.append(f"files[{i}] {path}: {fb}")
            continue

        # Scope: area.
        area = _area_of(path)
        if area not in c.allowed_areas:
            violations.append(
                f"files[{i}] {path}: area '{area}' not in allowed_areas {c.allowed_areas}"
            )

        # Action sanity.
        if action not in {"replace", "create", "delete"}:
            violations.append(f"files[{i}] {path}: unknown action '{entry.get('action')}'")
            continue
        if action in {"replace", "create"} and not isinstance(content, str):
            violations.append(f"files[{i}] {path}: new_content must be a string for action={action}")
            continue

        # No-new-top-level-dirs rule.
        if c.no_new_top_level_dirs and action == "create":
            top = Path(path).parts[0]
            if top and top not in existing_top and "/" in path.replace("\\", "/"):
                violations.append(
                    f"files[{i}] {path}: would create new top-level dir '{top}' (disabled)"
                )

        # Replace target should exist (warn-not-block to allow LLM corrections).
        if action == "replace":
            if not (workspace / path).exists():
                # Treat replace-of-missing as create for counting purposes.
                action = "create"

        if action == "create":
            n_new += 1

        # Secret scan in content.
        if action != "delete":
            secret = _is_secret_content(content)
            if secret is not None:
                violations.append(
                    f"files[{i}] {path}: content matches secret pattern ({secret})"
                )
            # LOC count (replace counts the WHOLE file, delete counts old size).
            n_loc += content.count("\n") + 1

        if action == "delete":
            p = workspace / path
            if p.exists() and p.is_file():
                try:
                    n_loc += sum(1 for _ in p.read_text("utf-8", "replace").splitlines()) or 1
                except Exception:
                    n_loc += 1

        n_total += 1

    if n_total > c.max_files_changed:
        violations.append(
            f"too many files changed: {n_total} > max_files_changed={c.max_files_changed}"
        )
    if n_new > c.max_new_files:
        violations.append(
            f"too many new files: {n_new} > max_new_files={c.max_new_files}"
        )
    if n_loc > c.max_total_loc_changed:
        violations.append(
            f"loc budget exceeded: ~{n_loc} > max_total_loc_changed={c.max_total_loc_changed}"
        )

    # Dep changes.
    npm_deps = manifest.get("add_npm_deps") or []
    pip_deps = manifest.get("add_pip_deps") or []
    if npm_deps and not c.allow_npm_deps_changes:
        violations.append("npm dep changes are disabled by project constraints")
    if pip_deps and not c.allow_pip_deps_changes:
        violations.append("pip dep changes are disabled by project constraints")
    if len(npm_deps) > c.max_new_npm_deps:
        violations.append(
            f"too many new npm deps: {len(npm_deps)} > max_new_npm_deps={c.max_new_npm_deps}"
        )
    if len(pip_deps) > c.max_new_pip_deps:
        violations.append(
            f"too many new pip deps: {len(pip_deps)} > max_new_pip_deps={c.max_new_pip_deps}"
        )

    stats = {
        "files_total": n_total,
        "files_new": n_new,
        "lines_estimated": n_loc,
        "npm_deps_added": len(npm_deps) if isinstance(npm_deps, list) else 0,
        "pip_deps_added": len(pip_deps) if isinstance(pip_deps, list) else 0,
    }

    return (len(violations) == 0, violations, stats)


def summarize_for_prompt(constraints: dict[str, Any] | None) -> str:
    """Produce a short human/LLM-readable block describing current constraints.
    Used inside the Improve prompt to make the LLM honour them up front."""
    c = ProjectConstraints.from_dict(constraints or {})
    return (
        "You MUST honour the following bounded-customization constraints:\n"
        f"- max_files_changed: {c.max_files_changed}\n"
        f"- max_new_files: {c.max_new_files}\n"
        f"- max_total_loc_changed: {c.max_total_loc_changed}\n"
        f"- allowed_areas: {', '.join(c.allowed_areas)}\n"
        f"- no_new_top_level_dirs: {c.no_new_top_level_dirs}\n"
        f"- allow_npm_deps_changes: {c.allow_npm_deps_changes} (max {c.max_new_npm_deps})\n"
        f"- allow_pip_deps_changes: {c.allow_pip_deps_changes} (max {c.max_new_pip_deps})\n"
        "Hard rules (non-negotiable):\n"
        "- Never edit .env, .env.*, .factory, node_modules, dist, build, .git\n"
        "- Never write any secret/key/token in file contents\n"
        "- All paths must remain inside the workspace\n"
    )
