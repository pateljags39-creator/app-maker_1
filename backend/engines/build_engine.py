"""Build engine: runs real frontend (npm) and backend (python import) builds inside the container.

Returns honest structured BuildRecord objects. Never fakes a pass.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("engines.build_engine")


@dataclass
class StepResult:
    name: str
    cmd: list[str]
    cwd: str
    returncode: int
    duration_s: float
    stdout_tail: str  # last ~4 KB
    stderr_tail: str  # last ~4 KB
    skipped: bool = False
    reason: str = ""

    @property
    def passed(self) -> bool:
        return self.returncode == 0 and not self.skipped


@dataclass
class BuildRecord:
    project_id: str
    workspace: str
    started_at: float
    finished_at: float
    overall_status: str  # PASS | PARTIAL | FAIL
    frontend: list[StepResult] = field(default_factory=list)
    backend: list[StepResult] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)  # e.g., {'frontend_dist': str}
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            **{k: v for k, v in asdict(self).items() if k not in ("frontend", "backend")},
            "frontend": [asdict(s) for s in self.frontend],
            "backend": [asdict(s) for s in self.backend],
        }


# ---------- helpers ----------
def _tail(s: str, n: int = 4096) -> str:
    if s is None:
        return ""
    return s[-n:] if len(s) > n else s


async def _run(
    cmd: list[str],
    cwd: Path,
    name: str,
    timeout: int = 600,
    env_extra: dict[str, str] | None = None,
) -> StepResult:
    if not cwd.exists():
        return StepResult(
            name=name, cmd=cmd, cwd=str(cwd),
            returncode=127, duration_s=0.0,
            stdout_tail="", stderr_tail=f"cwd missing: {cwd}",
            skipped=True, reason="missing_dir",
        )
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    start = time.monotonic()
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return StepResult(
                name=name, cmd=cmd, cwd=str(cwd),
                returncode=124, duration_s=time.monotonic() - start,
                stdout_tail="", stderr_tail=f"TIMEOUT after {timeout}s",
            )
        return StepResult(
            name=name, cmd=cmd, cwd=str(cwd),
            returncode=proc.returncode if proc.returncode is not None else -1,
            duration_s=time.monotonic() - start,
            stdout_tail=_tail((stdout or b"").decode("utf-8", "replace")),
            stderr_tail=_tail((stderr or b"").decode("utf-8", "replace")),
        )
    except FileNotFoundError as e:
        return StepResult(
            name=name, cmd=cmd, cwd=str(cwd),
            returncode=127, duration_s=time.monotonic() - start,
            stdout_tail="", stderr_tail=f"executable_missing: {e}",
        )


# ---------- public API ----------
async def build_frontend(workspace: Path, project_id: str) -> list[StepResult]:
    """Run npm install + npm run build (or vite build) inside workspace/frontend."""
    fe = workspace / "frontend"
    results: list[StepResult] = []
    if not fe.exists():
        results.append(StepResult(
            name="frontend.install", cmd=[], cwd=str(fe),
            returncode=0, duration_s=0.0,
            stdout_tail="", stderr_tail="",
            skipped=True, reason="no_frontend_dir",
        ))
        return results

    # 1) install
    #    Prefer `npm ci` (deterministic, fast) only when package-lock.json is fresh.
    #    A lock is "fresh" iff:
    #      - it exists,
    #      - its mtime >= package.json mtime (no edits to package.json since lock was regenerated),
    #      - it actually mentions every dependency declared in package.json.
    #    Otherwise the lock is stale (typical case: deterministic-deps fixup or LLM repair
    #    added a dep to package.json after a previous install) and `npm ci` would refuse to
    #    update it, causing builds to fail with "Rollup failed to resolve import ...".
    #    In that case delete the stale lock and run `npm install` so npm regenerates it.
    install_cmd = ["npm", "install", "--no-audit", "--no-fund", "--loglevel=error", "--prefer-offline"]
    lock = fe / "package-lock.json"
    pjson = fe / "package.json"
    use_ci = False
    if lock.exists() and pjson.exists():
        try:
            lock_fresh_by_mtime = lock.stat().st_mtime >= pjson.stat().st_mtime - 1.0  # 1s tolerance
            import json as _json
            pkg = _json.loads(pjson.read_text(encoding="utf-8"))
            declared = set((pkg.get("dependencies") or {}).keys()) | set((pkg.get("devDependencies") or {}).keys())
            lock_text = lock.read_text(encoding="utf-8", errors="replace")
            all_present = all(f'"node_modules/{d}"' in lock_text or f'"{d}"' in lock_text for d in declared)
            use_ci = lock_fresh_by_mtime and all_present
        except Exception:
            use_ci = False
    if use_ci:
        install_cmd = ["npm", "ci", "--no-audit", "--no-fund", "--loglevel=error", "--prefer-offline"]
    elif lock.exists():
        # Stale lock — remove it so npm install can regenerate a consistent lockfile.
        try:
            lock.unlink()
        except Exception:
            pass
    results.append(await _run(install_cmd, fe, "frontend.install", timeout=600))

    if results[-1].returncode != 0:
        return results

    # 2) build
    results.append(await _run(["npm", "run", "build"], fe, "frontend.build", timeout=600))
    return results


async def build_backend(workspace: Path, project_id: str) -> list[StepResult]:
    """Run pip install + python import-check inside workspace/backend."""
    be = workspace / "backend"
    results: list[StepResult] = []
    if not be.exists():
        results.append(StepResult(
            name="backend.install", cmd=[], cwd=str(be),
            returncode=0, duration_s=0.0,
            stdout_tail="", stderr_tail="",
            skipped=True, reason="no_backend_dir",
        ))
        return results

    req = be / "requirements.txt"
    if req.exists():
        results.append(await _run(
            ["pip", "install", "-q", "--disable-pip-version-check", "--no-input", "-r", "requirements.txt"],
            be, "backend.install", timeout=900,
        ))
        if results[-1].returncode != 0:
            return results
    else:
        results.append(StepResult(
            name="backend.install", cmd=[], cwd=str(be),
            returncode=0, duration_s=0.0,
            stdout_tail="", stderr_tail="",
            skipped=True, reason="no_requirements_txt",
        ))

    # 2) import check: pick main entry. Prefer main.py, then app.py, then server.py
    entry = None
    for cand in ("main.py", "app.py", "server.py"):
        if (be / cand).exists():
            entry = cand
            break
    if not entry:
        results.append(StepResult(
            name="backend.import", cmd=[], cwd=str(be),
            returncode=1, duration_s=0.0,
            stdout_tail="", stderr_tail="no backend entry file (main.py/app.py/server.py)",
        ))
        return results

    module = entry.removesuffix(".py")
    results.append(await _run(
        ["python", "-c", f"import importlib,sys; sys.path.insert(0,'.'); m=importlib.import_module('{module}'); print('imported', m.__name__)"],
        be, "backend.import", timeout=120,
    ))
    return results


async def run_build(workspace: Path, project_id: str) -> BuildRecord:
    started = time.time()
    fe_results, be_results = await asyncio.gather(
        build_frontend(workspace, project_id),
        build_backend(workspace, project_id),
    )
    finished = time.time()

    fe_pass = all(s.passed or s.skipped for s in fe_results) and any(s.passed for s in fe_results)
    be_pass = all(s.passed or s.skipped for s in be_results) and any(s.passed for s in be_results)

    if fe_pass and be_pass:
        overall = "PASS"
    elif fe_pass or be_pass:
        overall = "PARTIAL"
    else:
        overall = "FAIL"

    artifacts: dict[str, Any] = {}
    dist = workspace / "frontend" / "dist"
    if dist.exists():
        artifacts["frontend_dist"] = str(dist)
        artifacts["frontend_dist_files"] = sum(1 for _ in dist.rglob("*") if _.is_file())
    build_out = workspace / "frontend" / "build"
    if build_out.exists():
        artifacts["frontend_build"] = str(build_out)

    record = BuildRecord(
        project_id=project_id,
        workspace=str(workspace),
        started_at=started,
        finished_at=finished,
        overall_status=overall,
        frontend=fe_results,
        backend=be_results,
        artifacts=artifacts,
        summary={
            "frontend_pass": fe_pass,
            "backend_pass": be_pass,
            "duration_s": round(finished - started, 2),
        },
    )
    # Persist a build record into workspace/.factory/builds/<ts>.json
    factory = workspace / ".factory" / "builds"
    factory.mkdir(parents=True, exist_ok=True)
    out = factory / f"build-{int(started)}.json"
    out.write_text(json.dumps(record.to_dict(), indent=2))
    return record
