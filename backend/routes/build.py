"""Routes: build runs + repair history + acceptance."""
from __future__ import annotations

import asyncio
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, HTTPException

from engines.acceptance_engine import run_acceptance
from engines.build_engine import run_build
from engines.llm_gateway import LLMGateway
from engines.repair_engine import attempt_repairs
from event_ledger import get_ledger
import repositories as repo

router = APIRouter(prefix="/projects/{project_id}", tags=["build"])

_build_tasks: dict[str, asyncio.Task] = {}


async def _do_build(project_id: str) -> None:
    led = get_ledger()
    proj = await repo.get_project(project_id)
    if not proj:
        return
    ws = Path(proj["workspace_dir"])
    if not ws.exists():
        await led.emit_simple(project_id, "build.error", "workspace missing", severity="error")
        return
    try:
        await led.emit_simple(project_id, "build.started", "Manual build run", severity="info")
        await repo.set_state(project_id, "Building")
        build = await run_build(ws, project_id)
        repair_dict: dict = {}
        if build.overall_status != "PASS":
            await led.emit_simple(project_id, "repair.started", "Attempting repairs", severity="warning")
            gw = LLMGateway()
            constraints = await repo.get_constraints(project_id)
            build, outcome = await attempt_repairs(
                ws, project_id, gw, max_retries=2,
                initial_build=build, constraints=constraints,
            )
            repair_dict = outcome.to_dict()
            for a in outcome.attempts:
                await led.emit_simple(project_id, "repair.attempt",
                                      f"Attempt {a.attempt}: {a.classification} -> {a.build_after}",
                                      payload={"file": a.target_file, "applied": a.patch_applied,
                                              "note": a.note[:200]},
                                      severity="info" if a.patch_applied else "warning")
        await repo.add_build(project_id, build.to_dict(), repair_dict)
        await repo.update_project(project_id, last_build_status=build.overall_status)
        await led.emit_simple(project_id, "build.completed",
                              f"Build {build.overall_status}",
                              payload={"status": build.overall_status, "summary": build.summary},
                              severity="success" if build.overall_status == "PASS" else "warning")
        # Run acceptance pipeline as a follow-up
        brd_doc = await repo.get_brd(project_id)
        arch_doc = await repo.get_architecture(project_id)
        brd = (brd_doc or {}).get("brd") or {}
        arch = (arch_doc or {}).get("decision") or {}
        if brd and arch:
            await repo.set_state(project_id, "Acceptance")
            report = run_acceptance(ws, brd, arch, build_summary=build.to_dict())
            await repo.add_acceptance(project_id, report.to_dict())
            await repo.update_project(project_id, last_acceptance_status=report.overall)
            await led.emit_simple(project_id, "acceptance.completed",
                                  f"Acceptance {report.overall}",
                                  payload={"overall": report.overall}, severity="success")
    except Exception as e:
        await led.emit_simple(project_id, "build.error", f"{type(e).__name__}: {str(e)[:200]}", severity="error")
    finally:
        _build_tasks.pop(project_id, None)


@router.post("/build")
async def trigger_build(project_id: str):
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(404, "project_not_found")
    if project_id in _build_tasks and not _build_tasks[project_id].done():
        raise HTTPException(409, "build_already_running")
    t = asyncio.create_task(_do_build(project_id))
    _build_tasks[project_id] = t
    return {"status": "started"}


@router.get("/builds")
async def list_builds(project_id: str):
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(404, "project_not_found")
    builds = await repo.list_builds(project_id, limit=20)
    return {"builds": builds}
