"""HIGH-2 unit test: build_frontend must fall back to `npm install` when the
package-lock.json is stale (i.e. package.json was modified after the lock was
generated, OR the lock doesn't list every declared dependency).

This was the root cause of the user-reported "calculator made a mess" bug:
generation_engine._ensure_frontend_deps correctly added `uuid` to package.json
after the LLM forgot it, but the build engine ran `npm ci` against a stale
package-lock.json that didn't know about uuid, so Rollup failed with
`Failed to resolve import "uuid"`.

We exercise build_frontend with a controlled workspace and assert that:
  - stale lock + edited package.json   -> npm install used, stale lock removed
  - fresh lock matching package.json   -> npm ci used (fast path preserved)
  - missing dependency in lock         -> npm install used (defensive)
"""
import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engines import build_engine  # noqa: E402


def _make_workspace(deps: dict, lock_deps: list[str] | None, lock_older: bool) -> Path:
    """Create a synthetic workspace/frontend with controlled package.json and lock."""
    tmp = Path(tempfile.mkdtemp(prefix="bld-test-"))
    fe = tmp / "frontend"
    fe.mkdir(parents=True)
    pj = fe / "package.json"
    pj.write_text(json.dumps({"name": "t", "version": "0.0.0", "dependencies": deps}, indent=2))
    if lock_deps is not None:
        lock = fe / "package-lock.json"
        # Lockfile shape that includes each dep under packages map (npm v7+).
        lock_body = {
            "name": "t", "version": "0.0.0", "lockfileVersion": 3, "requires": True,
            "packages": {f"node_modules/{d}": {"version": "0.0.0"} for d in lock_deps},
        }
        lock.write_text(json.dumps(lock_body, indent=2))
        if lock_older:
            old = time.time() - 60
            os.utime(lock, (old, old))
            # touch package.json to be newer
            now = time.time()
            os.utime(pj, (now, now))
        else:
            # Touch lock to be newer than pj
            os.utime(pj, (time.time() - 60, time.time() - 60))
            os.utime(lock, (time.time(), time.time()))
    return tmp


async def _run(workspace: Path) -> list:
    """Run build_frontend with a stubbed _run that records the first install cmd."""
    recorded: list[list[str]] = []

    async def fake_run(cmd, cwd, name, timeout=600):
        recorded.append(list(cmd))
        # short-circuit: succeed on install, never get to build (we don't care)
        from engines.build_engine import StepResult
        return StepResult(
            name=name, cmd=list(cmd), cwd=str(cwd),
            returncode=0 if name == "frontend.install" else 1,
            duration_s=0.0, stdout_tail="", stderr_tail="",
        )

    with patch.object(build_engine, "_run", new=AsyncMock(side_effect=fake_run)):
        await build_engine.build_frontend(workspace, "test-proj")
    return recorded


def test_stale_lock_falls_back_to_npm_install():
    ws = _make_workspace(deps={"react": "^18", "uuid": "^9"}, lock_deps=["react"], lock_older=True)
    cmds = asyncio.get_event_loop().run_until_complete(_run(ws))
    assert cmds and cmds[0][0:2] == ["npm", "install"], f"expected npm install on stale lock, got {cmds[0]}"
    # And the stale lock should have been removed before install
    assert not (ws / "frontend" / "package-lock.json").exists(), "stale lock should have been deleted"
    print("OK: stale lock -> npm install (and lock deleted)")


def test_lock_missing_declared_dep_falls_back_to_npm_install():
    # Lock is "fresh" by mtime but doesn't include `uuid` declared in package.json.
    ws = _make_workspace(deps={"react": "^18", "uuid": "^9"}, lock_deps=["react"], lock_older=False)
    cmds = asyncio.get_event_loop().run_until_complete(_run(ws))
    assert cmds and cmds[0][0:2] == ["npm", "install"], f"expected npm install when lock missing dep, got {cmds[0]}"
    print("OK: lock missing declared dep -> npm install")


def test_fresh_consistent_lock_uses_npm_ci():
    # Lock is newer and includes every declared dep
    ws = _make_workspace(deps={"react": "^18", "uuid": "^9"}, lock_deps=["react", "uuid"], lock_older=False)
    cmds = asyncio.get_event_loop().run_until_complete(_run(ws))
    assert cmds and cmds[0][0:2] == ["npm", "ci"], f"expected npm ci on fresh consistent lock, got {cmds[0]}"
    assert (ws / "frontend" / "package-lock.json").exists(), "fresh lock should NOT be deleted"
    print("OK: fresh consistent lock -> npm ci (fast path preserved)")


def test_no_lock_uses_npm_install():
    ws = _make_workspace(deps={"react": "^18"}, lock_deps=None, lock_older=False)
    cmds = asyncio.get_event_loop().run_until_complete(_run(ws))
    assert cmds and cmds[0][0:2] == ["npm", "install"], f"expected npm install when no lock, got {cmds[0]}"
    print("OK: no lock -> npm install")


if __name__ == "__main__":
    test_stale_lock_falls_back_to_npm_install()
    test_lock_missing_declared_dep_falls_back_to_npm_install()
    test_fresh_consistent_lock_uses_npm_ci()
    test_no_lock_uses_npm_install()
    print("All HIGH-2 stale-lockfile tests passed.")
