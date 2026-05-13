"""Routes: project plan generation."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from engines.generation_engine import generate_plan
from engines.llm_gateway import LLMGateway
from event_ledger import get_ledger
import repositories as repo

router = APIRouter(prefix="/projects/{project_id}/plan", tags=["plan"])


@router.post("")
async def make_plan(project_id: str):
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(404, "project_not_found")
    brd_doc = await repo.get_brd(project_id)
    arch_doc = await repo.get_architecture(project_id)
    if not brd_doc or not (brd_doc.get("brd") or {}).get("requirements"):
        raise HTTPException(400, "brd_not_ready")
    if not arch_doc or not (arch_doc.get("decision") or {}).get("kind"):
        raise HTTPException(400, "architecture_not_detected")
    decision = arch_doc["decision"]
    if decision.get("blocked"):
        raise HTTPException(409, f"architecture_blocked: {decision.get('block_reasons')}")
    gw = LLMGateway()
    plan = await generate_plan(gw, brd_doc["brd"], decision)
    out = await repo.upsert_plan(project_id, plan)
    await repo.set_state(project_id, "Plan")
    await get_ledger().emit_simple(
        project_id=project_id, type="plan.generated",
        message=f"Plan with {len(plan.get('files', []))} files",
        payload={"files": len(plan.get("files", [])), "endpoints": len(plan.get("endpoints", []))},
        severity="success",
    )
    return out


@router.get("")
async def get_plan(project_id: str):
    doc = await repo.get_plan(project_id)
    if not doc:
        return {"project_id": project_id, "plan": None}
    return doc
