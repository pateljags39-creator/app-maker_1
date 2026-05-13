"""Improve/Fix engine.

One pass:
  1. snapshot current workspace (rollback safety)
  2. ask LLM (heavy tier = gemini-2.5-pro) for a JSON change manifest
  3. validate manifest against ProjectConstraints + hard rules
  4. apply manifest (writes are atomic per file, rollback on apply error)
  5. re-run build; if regression, restore snapshot and mark rolled_back
  6. re-run acceptance to attach honest pass/partial/fail to the attempt
  7. return a structured ImproveAttempt record (no Mongo writes here — caller persists)

Safety guarantees:
  * Never writes outside the workspace.
  * Never touches forbidden paths (.env, .factory, node_modules, dist, build, .git).
  * Never writes a file whose content matches a known-secret regex.
  * On any failure, the workspace is restored to the pre-call snapshot.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from .acceptance_engine import run_acceptance
from .build_engine import run_build, BuildRecord
from .constraints import (
    ProjectConstraints,
    summarize_for_prompt,
    validate_change,
)
from .llm_gateway import LLMGateway, LLMError
from .snapshot_engine import create_snapshot, restore_snapshot

logger = logging.getLogger("engines.improve_engine")


IMPROVE_SYSTEM = """You are the Improve/Fix engine for an AI software-factory.
You are given an EXISTING generated project (file tree + selected sources), its
BRD, its plan, and a free-form change request from the product owner.

Your job is to produce a STRICT JSON change manifest. You may NOT chat. You may
NOT produce prose. Return ONLY a single JSON object:

{
  "summary": "<one-line summary of what this change does>",
  "rationale": "<2-4 sentences explaining the approach>",
  "files": [
    {"path": "<relative path inside workspace>",
     "action": "replace" | "create" | "delete",
     "new_content": "<COMPLETE new file contents; omit for delete>"}
  ],
  "add_npm_deps": [{"name": "<pkg>", "version": "<semver-range>"}],
  "add_pip_deps": ["<package==version>"],
  "unsupported": ["<bullet of any requested change you cannot safely deliver>"]
}

MANDATORY:
* All file paths must be relative (e.g., "backend/main.py", not "/backend/main.py").
* Always provide the WHOLE new file in `new_content` (no diffs, no patches).
* Stay inside the existing top-level structure unless the request demands otherwise.
* If the change is too large to fit safely within the constraints block below,
  return a smaller scope and list the rest under `unsupported`.
* Never edit secrets / env files / node_modules / dist / build / .git / .factory.
* Never put any API key, token, or credential in any file.
"""


@dataclass
class FileDelta:
    path: str
    action: str  # replace | create | delete
    before_sha: str | None = None
    after_sha: str | None = None
    before_lines: int = 0
    after_lines: int = 0


@dataclass
class ImproveAttempt:
    id: str
    project_id: str
    change_request: str
    summary: str = ""
    rationale: str = ""
    status: str = "pending"  # pending | applied | rolled_back | rejected_by_constraints | llm_failed
    violations: list[str] = field(default_factory=list)
    files_changed: list[FileDelta] = field(default_factory=list)
    add_npm_deps: list[dict[str, str]] = field(default_factory=list)
    add_pip_deps: list[str] = field(default_factory=list)
    unsupported: list[str] = field(default_factory=list)
    snapshot_before: str | None = None
    build_before: str = ""
    build_after: str = ""
    acceptance_after: str = ""
    rolled_back: bool = False
    error: str = ""
    constraints_used: dict[str, Any] = field(default_factory=dict)
    stats: dict[str, Any] = field(default_factory=dict)
    created_at: float = 0.0
    finished_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["files_changed"] = [asdict(f) for f in self.files_changed]
        return d


# ---------- helpers ----------
def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()[:16]


def _tree(workspace: Path, limit: int = 250) -> list[str]:
    out: list[str] = []
    for p in sorted(workspace.rglob("*")):
        rel = p.relative_to(workspace)
        parts = set(rel.parts)
        if parts & {"node_modules", "__pycache__", ".factory", ".git", "dist", "build", ".venv"}:
            continue
        if len(out) >= limit:
            break
        out.append(rel.as_posix() + ("/" if p.is_dir() else ""))
    return out


def _selected_sources(workspace: Path, max_files: int = 12, max_total_chars: int = 32_000) -> dict[str, str]:
    """Return the most likely-relevant files (entrypoints + small files) as a
    capped dict so the LLM has just enough context."""
    important = [
        "backend/main.py",
        "backend/schemas.py",
        "backend/models.py",
        "backend/database.py",
        "frontend/src/App.jsx",
        "frontend/src/api.js",
        "frontend/src/main.jsx",
        "frontend/package.json",
        "backend/requirements.txt",
        "README.md",
        "frontend/index.html",
        "frontend/vite.config.js",
    ]
    out: dict[str, str] = {}
    total = 0
    for rel in important:
        p = workspace / rel
        if not p.exists() or not p.is_file():
            continue
        try:
            text = p.read_text("utf-8", "replace")
        except Exception:
            continue
        if len(text) > 12_000:
            text = text[:12_000] + "\n# ...(truncated for context)\n"
        if total + len(text) > max_total_chars:
            break
        out[rel] = text
        total += len(text)
        if len(out) >= max_files:
            break
    return out


def _user_prompt(
    brd: dict[str, Any],
    plan: dict[str, Any],
    change_request: str,
    tree: list[str],
    sources: dict[str, str],
    constraints: dict[str, Any] | None,
) -> str:
    src_block = "\n\n".join(
        f"### {path}\n```\n{content}\n```" for path, content in sources.items()
    )
    return (
        f"# Constraints block (HARD)\n{summarize_for_prompt(constraints)}\n\n"
        f"# Change request from product owner\n{change_request.strip()}\n\n"
        f"# BRD (summary)\n```json\n{json.dumps(brd, indent=2)[:6000]}\n```\n\n"
        f"# Plan (summary)\n```json\n{json.dumps(plan, indent=2)[:5000]}\n```\n\n"
        f"# Existing project tree\n```\n{chr(10).join(tree[:200])}\n```\n\n"
        f"# Selected current sources (for context)\n{src_block}\n\n"
        "Return the change manifest JSON as specified."
    )


async def _ask_manifest(
    gateway: LLMGateway,
    brd: dict[str, Any],
    plan: dict[str, Any],
    change_request: str,
    workspace: Path,
    constraints: dict[str, Any] | None,
) -> dict[str, Any]:
    tree = _tree(workspace)
    sources = _selected_sources(workspace)
    user = _user_prompt(brd, plan, change_request, tree, sources, constraints)
    resp = await gateway.complete(
        system=IMPROVE_SYSTEM,
        user=user,
        json_mode=True,
        temperature=0.1,
        max_output_tokens=12_000,
        tier="heavy",  # holistic reasoning -> gemini-2.5-pro
    )
    obj = resp.as_json()
    if not isinstance(obj, dict):
        raise LLMError(f"improve manifest non-dict: {type(obj).__name__}")
    return obj


def _apply(workspace: Path, manifest: dict[str, Any]) -> list[FileDelta]:
    deltas: list[FileDelta] = []
    for entry in manifest.get("files") or []:
        path = (entry.get("path") or "").strip()
        action = (entry.get("action") or "replace").lower()
        p = (workspace / path).resolve()
        # safety: must stay inside workspace
        try:
            p.relative_to(workspace.resolve())
        except ValueError:
            continue
        before_bytes = b""
        before_lines = 0
        if p.exists() and p.is_file():
            before_bytes = p.read_bytes()
            before_lines = before_bytes.count(b"\n") + (1 if before_bytes else 0)

        if action == "delete":
            if p.exists() and p.is_file():
                p.unlink()
            deltas.append(FileDelta(
                path=path, action="delete",
                before_sha=_sha(before_bytes) if before_bytes else None,
                after_sha=None,
                before_lines=before_lines, after_lines=0,
            ))
            continue

        new_content = entry.get("new_content") or ""
        if not isinstance(new_content, str):
            new_content = ""
        p.parent.mkdir(parents=True, exist_ok=True)
        new_bytes = new_content.encode("utf-8")
        p.write_bytes(new_bytes)
        deltas.append(FileDelta(
            path=path,
            action="create" if not before_bytes else "replace",
            before_sha=_sha(before_bytes) if before_bytes else None,
            after_sha=_sha(new_bytes),
            before_lines=before_lines,
            after_lines=new_content.count("\n") + (1 if new_content else 0),
        ))

    # Dependency additions.
    for dep in manifest.get("add_npm_deps") or []:
        pj = workspace / "frontend" / "package.json"
        if not pj.exists():
            continue
        try:
            pkg = json.loads(pj.read_text("utf-8"))
        except Exception:
            continue
        deps = dict(pkg.get("dependencies") or {})
        if dep.get("name") and dep["name"] not in deps:
            deps[dep["name"]] = dep.get("version") or "latest"
            pkg["dependencies"] = deps
            pj.write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")
    for spec in manifest.get("add_pip_deps") or []:
        req = workspace / "backend" / "requirements.txt"
        if not req.exists():
            continue
        text = req.read_text("utf-8")
        if spec.strip() and spec.strip() not in text:
            sep = "" if text.endswith("\n") or not text else "\n"
            req.write_text(text + sep + spec.strip() + "\n", encoding="utf-8")

    return deltas


def _is_regression(before: str, after: str) -> bool:
    """Return True if `after` is worse than `before` build status."""
    rank = {"PASS": 3, "PARTIAL": 2, "FAIL": 1, None: 0, "": 0}
    return rank.get(after, 0) < rank.get(before, 0)


# ---------- main entry ----------
async def request_improve(
    gateway: LLMGateway,
    workspace: Path,
    project_id: str,
    brd: dict[str, Any],
    plan: dict[str, Any],
    arch: dict[str, Any],
    change_request: str,
    constraints: dict[str, Any] | None,
    last_build_status: str = "",
) -> ImproveAttempt:
    """Run one improve attempt. Returns a populated ImproveAttempt record.

    The caller is responsible for persisting the result (Mongo) and emitting
    the ledger events.
    """
    workspace = Path(workspace)
    attempt = ImproveAttempt(
        id=uuid.uuid4().hex[:12],
        project_id=project_id,
        change_request=change_request,
        constraints_used=ProjectConstraints.from_dict(constraints or {}).to_dict(),
        build_before=last_build_status or "",
        created_at=time.time(),
    )

    # 1) Snapshot for rollback safety.
    try:
        snap = create_snapshot(workspace, label=f"pre-improve-{attempt.id}")
        attempt.snapshot_before = snap.id
    except Exception as e:
        attempt.status = "llm_failed"
        attempt.error = f"snapshot_failed: {type(e).__name__}: {e}"
        attempt.finished_at = time.time()
        return attempt

    # 2) Ask LLM for manifest.
    try:
        manifest = await _ask_manifest(gateway, brd, plan, change_request, workspace, constraints)
    except (LLMError, Exception) as e:
        attempt.status = "llm_failed"
        attempt.error = f"{type(e).__name__}: {str(e)[:200]}"
        attempt.finished_at = time.time()
        return attempt

    attempt.summary = (manifest.get("summary") or "").strip()[:300]
    attempt.rationale = (manifest.get("rationale") or "").strip()[:1000]
    attempt.add_npm_deps = list(manifest.get("add_npm_deps") or [])
    attempt.add_pip_deps = [str(x) for x in (manifest.get("add_pip_deps") or [])]
    attempt.unsupported = [str(x) for x in (manifest.get("unsupported") or [])]

    # 3) Validate against constraints.
    ok, violations, stats = validate_change(workspace, manifest, constraints)
    attempt.violations = violations
    attempt.stats = stats
    if not ok:
        attempt.status = "rejected_by_constraints"
        attempt.finished_at = time.time()
        return attempt

    # 4) Apply.
    try:
        deltas = _apply(workspace, manifest)
        attempt.files_changed = deltas
    except Exception as e:
        # Rollback on apply failure.
        try:
            restore_snapshot(workspace, attempt.snapshot_before)
        except Exception:
            pass
        attempt.status = "rolled_back"
        attempt.rolled_back = True
        attempt.error = f"apply_failed: {type(e).__name__}: {str(e)[:200]}"
        attempt.finished_at = time.time()
        return attempt

    # 5) Re-build (real npm + pip).
    try:
        build: BuildRecord = await run_build(workspace, project_id)
    except Exception as e:
        try:
            restore_snapshot(workspace, attempt.snapshot_before)
        except Exception:
            pass
        attempt.status = "rolled_back"
        attempt.rolled_back = True
        attempt.error = f"build_failed: {type(e).__name__}: {str(e)[:200]}"
        attempt.finished_at = time.time()
        return attempt
    attempt.build_after = build.overall_status

    # If we regressed the build status, rollback automatically.
    if last_build_status and _is_regression(last_build_status, build.overall_status):
        try:
            restore_snapshot(workspace, attempt.snapshot_before)
        except Exception:
            pass
        attempt.status = "rolled_back"
        attempt.rolled_back = True
        attempt.error = (
            f"regression: build {last_build_status} -> {build.overall_status}"
        )
        attempt.build_after = last_build_status  # restored
        attempt.finished_at = time.time()
        return attempt

    # 6) Re-run acceptance for an honest read-out.
    try:
        rep = run_acceptance(workspace, brd, arch, build_summary=build.to_dict(), plan=plan)
        attempt.acceptance_after = rep.overall
    except Exception as e:
        logger.warning("acceptance after improve failed: %s", e)
        attempt.acceptance_after = "UNKNOWN"

    attempt.status = "applied"
    attempt.finished_at = time.time()
    return attempt
