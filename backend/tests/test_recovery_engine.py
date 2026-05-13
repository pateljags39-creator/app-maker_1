"""Recovery engine: stale-pipeline sweep + manual recover."""
from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent.parent))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(HERE.parent.parent / ".env")

import db  # noqa: E402
import repositories as repo  # noqa: E402
from engines.recovery_engine import (  # noqa: E402
    manual_recover,
    sweep_stale_pipelines,
)


async def _seed(project_id: str, state: str, age_seconds: float = 0.0) -> None:
    db.init_client()
    mdb = db.get_db()
    await mdb.projects.delete_one({"id": project_id})
    await mdb.brds.delete_many({"project_id": project_id})
    await mdb.architectures.delete_many({"project_id": project_id})
    await mdb.plans.delete_many({"project_id": project_id})
    now = time.time() - age_seconds
    await mdb.projects.insert_one({
        "id": project_id,
        "name": f"recovery-smoke-{project_id}",
        "idea": "stuck-pipeline test",
        "state": state,
        "workspace_dir": f"/tmp/{project_id}",
        "brd_maturity": 0,
        "last_build_status": None,
        "ingested": False,
        "ingest_source": "",
        "ingest_status": "",
        "ingest_error": "",
        "created_at": now,
        "updated_at": now,
    })


async def _seed_with_brd(project_id: str, state: str, age_seconds: float) -> None:
    await _seed(project_id, state, age_seconds=age_seconds)
    await repo.upsert_brd(project_id, brd={
        "description": "BRD present",
        "requirements": [{"id": "R1", "text": "do something"}],
    }, maturity=50)


async def _cleanup(project_id: str) -> None:
    db.init_client()
    mdb = db.get_db()
    await mdb.projects.delete_one({"id": project_id})
    await mdb.brds.delete_many({"project_id": project_id})
    await mdb.architectures.delete_many({"project_id": project_id})
    await mdb.plans.delete_many({"project_id": project_id})
    await mdb.events.delete_many({"project_id": project_id})


async def test_sweep_recovers_stale_building() -> None:
    pid = "recover-test-stale-1"
    try:
        # Older than the 90s grace window.
        await _seed_with_brd(pid, "Building", age_seconds=200.0)
        recovered = await sweep_stale_pipelines()
        ids = {r["project_id"] for r in recovered}
        assert pid in ids, f"sweep did not recover {pid}: {ids}"
        proj = await repo.get_project(pid)
        assert proj["state"] == "BRD", f"expected BRD recovery, got {proj['state']}"
        print(f"OK: stale Building (BRD-only) recovered to {proj['state']}")
    finally:
        await _cleanup(pid)


async def test_sweep_skips_fresh() -> None:
    pid = "recover-test-fresh-2"
    try:
        await _seed_with_brd(pid, "Building", age_seconds=5.0)
        recovered = await sweep_stale_pipelines()
        ids = {r["project_id"] for r in recovered}
        assert pid not in ids, f"sweep wrongly recovered fresh project {pid}"
        proj = await repo.get_project(pid)
        assert proj["state"] == "Building", proj["state"]
        print("OK: fresh project within grace window left untouched")
    finally:
        await _cleanup(pid)


async def test_manual_recover_returns_noop_when_not_stuck() -> None:
    pid = "recover-test-noop-3"
    try:
        await _seed(pid, "Idea", age_seconds=5.0)
        out = await manual_recover(pid)
        assert out and out["reason"] == "no_op_not_stuck", out
        print("OK: manual_recover no-op when project not in transient state")
    finally:
        await _cleanup(pid)


async def test_manual_recover_unsticks_building() -> None:
    pid = "recover-test-manual-4"
    try:
        await _seed_with_brd(pid, "Building", age_seconds=120.0)
        out = await manual_recover(pid)
        assert out and out["previous_state"] == "Building", out
        assert out["recovered_state"] == "BRD", out
        proj = await repo.get_project(pid)
        assert proj["state"] == "BRD", proj["state"]
        print(f"OK: manual_recover unstuck Building -> {proj['state']}")
    finally:
        await _cleanup(pid)


async def main() -> int:
    await test_sweep_recovers_stale_building()
    await test_sweep_skips_fresh()
    await test_manual_recover_returns_noop_when_not_stuck()
    await test_manual_recover_unsticks_building()
    print("All recovery_engine tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
