"""Routes: BRD intake (questions + answers + derive + maturity)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from engines.brd_engine import derive_brd, generate_questions
from engines.llm_gateway import LLMGateway
from event_ledger import get_ledger
from orchestrator_models import AnswerSubmission
import repositories as repo

router = APIRouter(prefix="/projects/{project_id}/brd", tags=["brd"])


class AnswerBatch(BaseModel):
    answers: list[AnswerSubmission]


@router.post("/questions")
async def create_questions(project_id: str):
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(404, "project_not_found")
    gw = LLMGateway()
    prior = (await repo.get_brd(project_id)) or {}
    qs = await generate_questions(gw, proj["idea"], prior.get("brd"))
    brd_doc = await repo.upsert_brd(project_id, questions=qs, brd=prior.get("brd", {}),
                                    answers=prior.get("answers", []), maturity=prior.get("maturity", 0))
    await repo.set_state(project_id, "BRD")
    await get_ledger().emit_simple(
        project_id=project_id, type="brd.questions.generated",
        message=f"{len(qs)} SME questions generated",
        payload={"count": len(qs)}, severity="info",
    )
    return brd_doc


@router.get("")
async def get_brd(project_id: str):
    doc = await repo.get_brd(project_id)
    if not doc:
        return {"project_id": project_id, "questions": [], "answers": [], "brd": {}, "maturity": 0}
    return doc


@router.post("/answers")
async def submit_answers(project_id: str, batch: AnswerBatch):
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(404, "project_not_found")
    prior = (await repo.get_brd(project_id)) or {}
    prev_answers = [a if isinstance(a, dict) else a.model_dump() for a in prior.get("answers", [])]
    new_pairs = [a.model_dump() for a in batch.answers]
    # Merge by question_id
    by_id = {a["question_id"]: a for a in prev_answers}
    for a in new_pairs:
        by_id[a["question_id"]] = a
    merged = list(by_id.values())

    gw = LLMGateway()
    brd = await derive_brd(gw, proj["idea"], merged, prior.get("brd"))
    maturity = int((brd.get("maturity") or {}).get("score", 0) or 0)
    doc = await repo.upsert_brd(
        project_id,
        questions=prior.get("questions", []),
        answers=merged,
        brd=brd,
        maturity=maturity,
    )
    await repo.update_project(project_id, brd_maturity=maturity)
    await get_ledger().emit_simple(
        project_id=project_id, type="brd.derived",
        message=f"BRD updated; maturity {maturity}",
        payload={"maturity": maturity, "reqs": len(brd.get("requirements", []))},
        severity="success" if maturity >= 60 else "info",
    )
    return doc
