"""Routes: acceptance run + report."""
from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, HTTPException

from engines.acceptance_engine import run_acceptance
from event_ledger import get_ledger
import repositories as repo

router = APIRouter(prefix="/projects/{project_id}/acceptance", tags=["acceptance"])


@router.post("")
async def run(project_id: str):
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(404, "project_not_found")
    ws = Path(proj["workspace_dir"])
    brd_doc = await repo.get_brd(project_id)
    arch_doc = await repo.get_architecture(project_id)
    plan_doc = await repo.get_plan(project_id)
    brd = (brd_doc or {}).get("brd") or {}
    arch = (arch_doc or {}).get("decision") or {}
    plan = (plan_doc or {}).get("plan") or {}
    builds = await repo.list_builds(project_id, limit=1)
    build_summary = builds[0]["build"] if builds else None
    report = run_acceptance(ws, brd, arch, build_summary=build_summary, plan=plan)
    await repo.add_acceptance(project_id, report.to_dict())
    await repo.update_project(project_id, last_acceptance_status=report.overall)
    await get_ledger().emit_simple(
        project_id=project_id, type="acceptance.completed",
        message=f"Acceptance {report.overall}", payload={"overall": report.overall},
        severity="success" if report.overall == "PASS" else "warning",
    )
    return report.to_dict()


@router.get("")
async def latest(project_id: str):
    doc = await repo.latest_acceptance(project_id)
    if not doc:
        return {"project_id": project_id, "report": None}
    return doc
