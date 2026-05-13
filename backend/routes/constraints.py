"""Routes: per-project bounded-customization constraints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from engines.constraints import ProjectConstraints, default_constraints
from event_ledger import get_ledger
import repositories as repo

router = APIRouter(prefix="/projects/{project_id}/constraints", tags=["constraints"])


@router.get("")
async def get_constraints(project_id: str):
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(404, "project_not_found")
    c = await repo.get_constraints(project_id)
    return {"project_id": project_id, "constraints": c or default_constraints()}


@router.put("")
async def put_constraints(project_id: str, payload: dict):
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(404, "project_not_found")
    # Normalize through the dataclass so we strip unknown keys and coerce types.
    body = payload.get("constraints", payload)
    c = ProjectConstraints.from_dict(body).to_dict()
    saved = await repo.set_constraints(project_id, c)
    await get_ledger().emit_simple(
        project_id=project_id, type="constraints.updated",
        message="Bounded-customization constraints updated",
        payload={"max_files_changed": c["max_files_changed"],
                 "allowed_areas": c["allowed_areas"]},
        severity="info",
    )
    return {"project_id": project_id, "constraints": saved}


@router.post("/reset")
async def reset_constraints(project_id: str):
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(404, "project_not_found")
    c = default_constraints()
    saved = await repo.set_constraints(project_id, c)
    await get_ledger().emit_simple(
        project_id=project_id, type="constraints.reset",
        message="Constraints reset to defaults",
        payload={}, severity="info",
    )
    return {"project_id": project_id, "constraints": saved}
