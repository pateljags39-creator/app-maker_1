"""Routes: Improve/Fix workflow on an existing generated project."""
from __future__ import annotations

import asyncio
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from engines.improve_engine import request_improve
from engines.llm_gateway import LLMGateway
from event_ledger import get_ledger
import repositories as repo

router = APIRouter(prefix="/projects/{project_id}/improve", tags=["improve"])


class ImproveRequest(BaseModel):
    change_request: str = Field(..., min_length=4, max_length=4000)


@router.post("")
async def make_improve(project_id: str, payload: ImproveRequest):
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(404, "project_not_found")
    ws = Path(proj["workspace_dir"])
    if not ws.exists():
        raise HTTPException(400, "workspace_missing")

    brd_doc = await repo.get_brd(project_id)
    arch_doc = await repo.get_architecture(project_id)
    plan_doc = await repo.get_plan(project_id)
    if not (brd_doc and arch_doc and plan_doc):
        raise HTTPException(400, "project_not_generated_yet")

    brd = brd_doc.get("brd") or {}
    arch = arch_doc.get("decision") or {}
    plan = plan_doc.get("plan") or {}
    constraints = await repo.get_constraints(project_id)
    last_build_status = (proj.get("last_build_status") or "").upper()

    await get_ledger().emit_simple(
        project_id=project_id, type="improve.requested",
        message=f"Improve requested: {payload.change_request[:80]}",
        payload={"len": len(payload.change_request)}, severity="info",
    )

    gw = LLMGateway()
    attempt = await request_improve(
        gateway=gw, workspace=ws, project_id=project_id,
        brd=brd, plan=plan, arch=arch,
        change_request=payload.change_request,
        constraints=constraints,
        last_build_status=last_build_status,
    )

    rec = await repo.add_improve_attempt(project_id, attempt.to_dict())

    # Ledger.
    sev = "success" if attempt.status == "applied" else (
        "warning" if attempt.status in {"rejected_by_constraints", "rolled_back"} else "error"
    )
    await get_ledger().emit_simple(
        project_id=project_id, type=f"improve.{attempt.status}",
        message=attempt.summary or attempt.error or attempt.status,
        payload={
            "id": attempt.id, "status": attempt.status,
            "files_changed": len(attempt.files_changed),
            "violations": len(attempt.violations),
            "build_after": attempt.build_after,
            "acceptance_after": attempt.acceptance_after,
            "rolled_back": attempt.rolled_back,
        }, severity=sev,
    )

    # Refresh denormalised project status if successful.
    if attempt.status == "applied":
        await repo.update_project(
            project_id,
            last_build_status=attempt.build_after,
            last_acceptance_status=attempt.acceptance_after,
        )

    return rec


@router.get("")
async def list_improves(project_id: str, limit: int = 30):
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(404, "project_not_found")
    return await repo.list_improve_attempts(project_id, limit=limit)


@router.get("/{attempt_id}")
async def get_improve(project_id: str, attempt_id: str):
    doc = await repo.get_improve_attempt(project_id, attempt_id)
    if not doc:
        raise HTTPException(404, "improve_attempt_not_found")
    return doc
