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

    # HIGH-1: if limited_prototype is accepted on frontend_only with backend signals,
    # propagate the honest "unsupported" status onto the affected BRD requirements
    # so plan/acceptance never silently claim coverage of un-buildable features.
    marked = 0
    if (
        decision["kind"] == "frontend_only"
        and decision["limited_prototype_accepted"]
        and decision["unsupported_requirement_indices"]
    ):
        reqs = list(brd.get("requirements") or [])
        keywords_csv = ", ".join(decision["unsupported_signal_keywords"]) or "backend"
        reason = (
            f"frontend_only limited_prototype: requires {keywords_csv} which is not "
            "deliverable in a frontend-only build."
        )
        for idx in decision["unsupported_requirement_indices"]:
            if 0 <= idx < len(reqs):
                req = reqs[idx]
                if isinstance(req, str):
                    req = {"text": req}
                if not isinstance(req, dict):
                    continue
                req["status"] = "unsupported"
                existing_reason = req.get("unsupported_reason") or req.get("block_reason")
                if not existing_reason:
                    req["unsupported_reason"] = reason
                reqs[idx] = req
                marked += 1
        if marked:
            brd["requirements"] = reqs
            await repo.upsert_brd(project_id, brd=brd)

    await get_ledger().emit_simple(
        project_id=project_id, type="architecture.overridden",
        message=(
            f"Override -> {decision['kind']} (limited_prototype={body.allow_limited_prototype}); "
            f"{marked} requirement(s) marked unsupported"
        ),
        payload={
            "kind": decision["kind"],
            "limited_prototype": body.allow_limited_prototype,
            "unsupported_marked": marked,
        },
        severity="warning" if marked else "info",
    )
    return out


@router.get("")
async def get_architecture(project_id: str):
    doc = await repo.get_architecture(project_id)
    if not doc:
        return {"project_id": project_id, "decision": None}
    return doc
