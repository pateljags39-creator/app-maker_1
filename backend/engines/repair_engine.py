"""Repair engine: classify build failures, ask LLM for SAFE single-file patches, apply, retry.

Hard rules:
- Only edit files inside the project's workspace.
- Never edit forbidden paths (.env*, .factory/*, node_modules, dist, build, .git).
- Each retry produces a repair record.
- If the patch fails to compile/build, rollback to the previous file content.
"""
from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .build_engine import BuildRecord, StepResult, run_build
from .llm_gateway import LLMGateway, LLMError

logger = logging.getLogger("engines.repair_engine")

FORBIDDEN_PARTS = {".env", ".env.local", ".env.production", ".factory", "node_modules", "dist", "build", ".git"}


@dataclass
class RepairAttempt:
    attempt: int
    started_at: float
    finished_at: float
    classification: str
    target_file: str
    target_step: str
    error_excerpt: str
    patch_applied: bool
    build_after: str  # PASS | PARTIAL | FAIL
    note: str = ""
    provider: str = ""


@dataclass
class RepairOutcome:
    final_status: str  # PASS | PARTIAL | FAIL
    attempts: list[RepairAttempt] = field(default_factory=list)
    rolled_back: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "final_status": self.final_status,
            "rolled_back": self.rolled_back,
            "attempts": [asdict(a) for a in self.attempts],
        }


# ---------- classification ----------
ERROR_TAXONOMY = [
    ("missing_module", re.compile(r"ModuleNotFoundError|Cannot find module|cannot resolve module", re.I)),
    ("vite_resolution", re.compile(r"Failed to resolve import|Could not resolve|Rollup failed to resolve", re.I)),
    ("import_error", re.compile(r"ImportError", re.I)),
    ("syntax_error", re.compile(r"SyntaxError|Unexpected token|parse error", re.I)),
    ("py_dep_conflict", re.compile(r"ResolutionImpossible|conflicting dependencies|cannot install", re.I)),
    ("py_missing_dep", re.compile(r"No matching distribution found|Could not find a version|ERROR: .*not found", re.I)),
    ("npm_missing_dep", re.compile(r"Missing\s+dependencies|npm\s+ERR!.*ENOENT|ETARGET", re.I)),
    ("port_in_use", re.compile(r"EADDRINUSE", re.I)),
    ("type_error", re.compile(r"TypeError|TS\d+", re.I)),
    ("json_invalid", re.compile(r"Unexpected token in JSON", re.I)),
]


def classify_error(text: str) -> str:
    for label, rx in ERROR_TAXONOMY:
        if rx.search(text):
            return label
    return "unknown"


def _safe_path(workspace: Path, rel: str) -> Path | None:
    p = (workspace / rel).resolve()
    try:
        p.relative_to(workspace.resolve())
    except ValueError:
        return None
    rel_parts = set(Path(rel).parts)
    if rel_parts & FORBIDDEN_PARTS:
        return None
    return p


def _guess_failing_file(workspace: Path, error_text: str) -> str | None:
    """Heuristic: find first existing relative file mentioned in the error."""
    candidates = re.findall(r"([\w./\-]+\.(?:py|js|jsx|ts|tsx|json|html|css))", error_text)
    for c in candidates:
        # strip leading ./
        c_clean = c.lstrip("./")
        for sub in (workspace / "backend", workspace / "frontend", workspace):
            p = sub / c_clean
            if p.exists() and p.is_file():
                return str(p.relative_to(workspace))
    return None


# ---------- LLM patch ----------
PATCH_SYSTEM = """You are a precise repair engine for an AI software-factory.
You will receive ONE failing build step's error output, the offending file's full contents, the build classification, and the project tree.
Return ONLY a JSON object:
{
  "action": "replace_file" | "replace_file_and_add_dep" | "replace_files" | "skip",
  "file_path": "<relative path from project root>",
  "new_content": "<full new file contents>",
  "additional_files": [{"file_path": "...", "new_content": "..."}],
  "add_npm_deps": [{"name": "...", "version": "^x.y.z"}],
  "add_pip_deps": ["package==x.y.z"],
  "rationale": "<one short sentence>"
}

Hard constraints:
- Never edit .env, .env.*, .factory, node_modules, dist, build, .git.
- Keep changes minimal and targeted.
- Do not introduce new architectural layers.
- If you cannot safely repair, use action="skip".
"""


async def _ask_patch(
    gateway: LLMGateway,
    classification: str,
    error_excerpt: str,
    target_rel: str | None,
    target_content: str | None,
    project_tree: list[str],
) -> dict[str, Any]:
    user = (
        f"# Classification\n{classification}\n\n"
        f"# Build error (tail)\n```\n{error_excerpt[-3500:]}\n```\n\n"
        f"# Project tree (relative)\n```\n{chr(10).join(project_tree[:200])}\n```\n\n"
        f"# Offending file path\n{target_rel or '(unknown)'}\n\n"
        f"# Offending file content (current)\n```\n{(target_content or '')[:8000]}\n```\n"
        "Return ONLY the JSON object as specified."
    )
    last_err: Exception | None = None
    for _ in range(2):
        try:
            resp = await gateway.complete(
                system=PATCH_SYSTEM,
                user=user,
                json_mode=True,
                temperature=0.0,
                max_output_tokens=8000,
                tier="heavy",  # patch synthesis must reason about file+error+tree -> gemini-2.5-pro
            )
            obj = resp.as_json()
            if isinstance(obj, dict):
                return obj
            last_err = LLMError(f"non-dict patch shape: {type(obj).__name__}")
        except Exception as e:
            last_err = e
            logger.warning("repair LLM parse failed: %s", e)
    assert last_err is not None
    raise last_err


def _tree(workspace: Path, limit: int = 300) -> list[str]:
    out: list[str] = []
    for p in sorted(workspace.rglob("*")):
        rel = p.relative_to(workspace)
        if set(rel.parts) & FORBIDDEN_PARTS:
            continue
        if len(out) >= limit:
            break
        out.append(rel.as_posix() + ("/" if p.is_dir() else ""))
    return out


# ---------- main loop ----------
async def attempt_repairs(
    workspace: Path,
    project_id: str,
    gateway: LLMGateway,
    max_retries: int = 2,
    initial_build: BuildRecord | None = None,
    constraints: dict | None = None,
) -> tuple[BuildRecord, RepairOutcome]:
    workspace = Path(workspace)
    outcome = RepairOutcome(final_status="FAIL")
    build = initial_build or await run_build(workspace, project_id)
    if build.overall_status == "PASS":
        outcome.final_status = "PASS"
        return build, outcome

    for attempt in range(1, max_retries + 1):
        # Pick the first failed step (frontend first, then backend) - typical signal there.
        failed_step: StepResult | None = None
        for s in build.frontend + build.backend:
            if not s.skipped and s.returncode != 0:
                failed_step = s
                break
        if failed_step is None:
            break

        err_text = (failed_step.stderr_tail or "") + "\n" + (failed_step.stdout_tail or "")
        classification = classify_error(err_text)
        target_rel = _guess_failing_file(workspace, err_text)
        target_path = _safe_path(workspace, target_rel) if target_rel else None
        target_content = target_path.read_text("utf-8", "replace") if target_path and target_path.exists() else None

        started = time.time()
        try:
            patch = await _ask_patch(
                gateway,
                classification=classification,
                error_excerpt=err_text,
                target_rel=target_rel,
                target_content=target_content,
                project_tree=_tree(workspace),
            )
        except (LLMError, Exception) as e:
            outcome.attempts.append(RepairAttempt(
                attempt=attempt, started_at=started, finished_at=time.time(),
                classification=classification, target_file=target_rel or "",
                target_step=failed_step.name, error_excerpt=err_text[-500:],
                patch_applied=False, build_after=build.overall_status,
                note=f"llm_error: {type(e).__name__}: {str(e)[:160]}",
            ))
            break

        action = patch.get("action", "skip")
        if action == "skip":
            outcome.attempts.append(RepairAttempt(
                attempt=attempt, started_at=started, finished_at=time.time(),
                classification=classification, target_file=target_rel or "",
                target_step=failed_step.name, error_excerpt=err_text[-500:],
                patch_applied=False, build_after=build.overall_status,
                note=f"llm_skip: {patch.get('rationale','no rationale')}",
            ))
            break

        # ----- bounded-customization gate (Phase 3b) -----
        # Convert the repair patch to a manifest shape and validate it against
        # the project's constraints. On violation, skip this attempt entirely
        # (we never silently apply over-budget repairs).
        if constraints:
            from .constraints import validate_change as _validate_change
            manifest_files = []
            if patch.get("file_path"):
                manifest_files.append({
                    "path": patch["file_path"],
                    "action": "replace",
                    "new_content": patch.get("new_content", ""),
                })
            for af in patch.get("additional_files") or []:
                if af.get("file_path"):
                    manifest_files.append({
                        "path": af["file_path"],
                        "action": "replace",
                        "new_content": af.get("new_content", ""),
                    })
            manifest = {
                "files": manifest_files,
                "add_npm_deps": patch.get("add_npm_deps") or [],
                "add_pip_deps": patch.get("add_pip_deps") or [],
            }
            ok_c, violations_c, _stats = _validate_change(workspace, manifest, constraints)
            if not ok_c:
                outcome.attempts.append(RepairAttempt(
                    attempt=attempt, started_at=started, finished_at=time.time(),
                    classification=classification, target_file=target_rel or "",
                    target_step=failed_step.name, error_excerpt=err_text[-500:],
                    patch_applied=False, build_after=build.overall_status,
                    note=f"rejected_by_constraints: {'; '.join(violations_c)[:240]}",
                ))
                break

        applied: list[tuple[Path, str | None]] = []  # (path, prev_content)
        try:
            # primary file
            file_path = patch.get("file_path") or target_rel
            if file_path:
                p = _safe_path(workspace, file_path)
                if p is None:
                    raise RuntimeError(f"unsafe_path: {file_path}")
                prev = p.read_text("utf-8", "replace") if p.exists() else None
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(patch.get("new_content", ""), encoding="utf-8")
                applied.append((p, prev))
            # additional files
            for af in patch.get("additional_files") or []:
                fp = af.get("file_path")
                if not fp:
                    continue
                p = _safe_path(workspace, fp)
                if p is None:
                    raise RuntimeError(f"unsafe_path: {fp}")
                prev = p.read_text("utf-8", "replace") if p.exists() else None
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(af.get("new_content", ""), encoding="utf-8")
                applied.append((p, prev))
            # npm deps
            for dep in patch.get("add_npm_deps") or []:
                pkg_path = workspace / "frontend" / "package.json"
                if pkg_path.exists():
                    pkg = json.loads(pkg_path.read_text())
                    prev = pkg_path.read_text()
                    pkg.setdefault("dependencies", {})[dep["name"]] = dep.get("version", "latest")
                    pkg_path.write_text(json.dumps(pkg, indent=2))
                    applied.append((pkg_path, prev))
            # pip deps
            for dep in patch.get("add_pip_deps") or []:
                req_path = workspace / "backend" / "requirements.txt"
                prev = req_path.read_text() if req_path.exists() else ""
                if dep not in prev:
                    req_path.write_text(prev + ("" if prev.endswith("\n") or not prev else "\n") + dep + "\n")
                    applied.append((req_path, prev))
        except Exception as e:
            # rollback partial changes
            for p, prev in applied:
                if prev is None and p.exists():
                    p.unlink()
                elif prev is not None:
                    p.write_text(prev, encoding="utf-8")
            outcome.attempts.append(RepairAttempt(
                attempt=attempt, started_at=started, finished_at=time.time(),
                classification=classification, target_file=target_rel or "",
                target_step=failed_step.name, error_excerpt=err_text[-500:],
                patch_applied=False, build_after=build.overall_status,
                note=f"apply_error: {type(e).__name__}: {str(e)[:160]}",
            ))
            break

        # rebuild
        new_build = await run_build(workspace, project_id)
        improved = new_build.overall_status in {"PASS", "PARTIAL"} and (
            (new_build.overall_status == "PASS" and build.overall_status != "PASS")
            or (new_build.overall_status == "PARTIAL" and build.overall_status == "FAIL")
        )
        if new_build.overall_status == "PASS" or improved:
            build = new_build
            outcome.attempts.append(RepairAttempt(
                attempt=attempt, started_at=started, finished_at=time.time(),
                classification=classification, target_file=target_rel or "",
                target_step=failed_step.name, error_excerpt=err_text[-500:],
                patch_applied=True, build_after=new_build.overall_status,
                note=patch.get("rationale", ""),
            ))
            if new_build.overall_status == "PASS":
                outcome.final_status = "PASS"
                return build, outcome
        else:
            # rollback this attempt's writes
            for p, prev in applied:
                if prev is None and p.exists():
                    p.unlink()
                elif prev is not None:
                    p.write_text(prev, encoding="utf-8")
            outcome.rolled_back = True
            outcome.attempts.append(RepairAttempt(
                attempt=attempt, started_at=started, finished_at=time.time(),
                classification=classification, target_file=target_rel or "",
                target_step=failed_step.name, error_excerpt=err_text[-500:],
                patch_applied=True, build_after=new_build.overall_status,
                note=f"rolled_back: no improvement (was {build.overall_status} -> {new_build.overall_status}); {patch.get('rationale','')}",
            ))
            # keep `build` pointing at the better state
    outcome.final_status = build.overall_status
    return build, outcome
