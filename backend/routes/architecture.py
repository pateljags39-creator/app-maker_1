"""Routes: architecture detection + override."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from engines.architecture_engine import detect_architecture
from event_ledger import get_ledger
from orchestrator_models import ArchitectureOverrideRequest
import repositories as repo

router = APIRouter(prefix="/projects/{project_id}/architecture", tags=["architecture"])


@router.post("/detect")
async def detect(project_id: str):
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(404, "project_not_found")
    brd_doc = await repo.get_brd(project_id)
    brd = (brd_doc or {}).get("brd") or {}
    decision = detect_architecture(brd).to_dict()
    out = await repo.upsert_architecture(project_id, decision)
    await repo.set_state(project_id, "Architecture")
    await get_ledger().emit_simple(
        project_id=project_id, type="architecture.detected",
        message=f"Architecture: {decision['kind']}",
        payload={"kind": decision["kind"], "blocked": decision["blocked"]},
        severity="warning" if decision["blocked"] else "success",
    )
    return out


@router.post("/override")
async def override(project_id: str, body: ArchitectureOverrideRequest):
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(404, "project_not_found")
    brd_doc = await repo.get_brd(project_id)
    brd = (brd_doc or {}).get("brd") or {}
    if body.forced_architecture:
        brd["forced_architecture"] = body.forced_architecture
    decision = detect_architecture(brd, allow_limited_prototype=body.allow_limited_prototype).to_dict()
    out = await repo.upsert_architecture(project_id, decision)
    await get_ledger().emit_simple(
        project_id=project_id, type="architecture.overridden",
        message=f"Override -> {decision['kind']} (limited_prototype={body.allow_limited_prototype})",
        payload={"kind": decision["kind"], "limited_prototype": body.allow_limited_prototype},
        severity="info",
    )
    return out


@router.get("")
async def get_architecture(project_id: str):
    doc = await repo.get_architecture(project_id)
    if not doc:
        return {"project_id": project_id, "decision": None}
    return doc
