"""Mongo CRUD helpers."""
from __future__ import annotations

from typing import Any

from db import get_db
from orchestrator_models import Project, ProjectState, now


async def list_projects() -> list[dict]:
    db = get_db()
    cursor = db.projects.find({}, {"_id": 0}).sort("updated_at", -1)
    return [d async for d in cursor]


async def get_project(project_id: str) -> dict | None:
    db = get_db()
    return await db.projects.find_one({"id": project_id}, {"_id": 0})


async def create_project(project: Project) -> dict:
    db = get_db()
    doc = project.model_dump()
    await db.projects.insert_one(doc)
    doc.pop("_id", None)
    return doc


async def update_project(project_id: str, **fields: Any) -> dict | None:
    db = get_db()
    fields["updated_at"] = now()
    await db.projects.update_one({"id": project_id}, {"$set": fields})
    return await get_project(project_id)


async def set_state(project_id: str, state: ProjectState) -> dict | None:
    return await update_project(project_id, state=state)


async def delete_project(project_id: str) -> int:
    db = get_db()
    res = await db.projects.delete_one({"id": project_id})
    await db.brds.delete_many({"project_id": project_id})
    await db.architectures.delete_many({"project_id": project_id})
    await db.plans.delete_many({"project_id": project_id})
    await db.builds.delete_many({"project_id": project_id})
    await db.acceptance.delete_many({"project_id": project_id})
    await db.exports.delete_many({"project_id": project_id})
    await db.events.delete_many({"project_id": project_id})
    await db.constraints.delete_many({"project_id": project_id})
    await db.improve_attempts.delete_many({"project_id": project_id})
    return res.deleted_count


async def upsert_brd(project_id: str, **fields: Any) -> dict:
    db = get_db()
    fields["project_id"] = project_id
    fields["updated_at"] = now()
    await db.brds.update_one({"project_id": project_id}, {"$set": fields}, upsert=True)
    doc = await db.brds.find_one({"project_id": project_id}, {"_id": 0})
    return doc or {}


async def get_brd(project_id: str) -> dict | None:
    db = get_db()
    return await db.brds.find_one({"project_id": project_id}, {"_id": 0})


async def upsert_architecture(project_id: str, decision: dict) -> dict:
    db = get_db()
    doc = {"project_id": project_id, "decision": decision, "updated_at": now()}
    await db.architectures.update_one({"project_id": project_id}, {"$set": doc}, upsert=True)
    out = await db.architectures.find_one({"project_id": project_id}, {"_id": 0})
    return out or {}


async def get_architecture(project_id: str) -> dict | None:
    db = get_db()
    return await db.architectures.find_one({"project_id": project_id}, {"_id": 0})


async def upsert_plan(project_id: str, plan: dict) -> dict:
    db = get_db()
    doc = {"project_id": project_id, "plan": plan, "updated_at": now()}
    await db.plans.update_one({"project_id": project_id}, {"$set": doc}, upsert=True)
    out = await db.plans.find_one({"project_id": project_id}, {"_id": 0})
    return out or {}


async def get_plan(project_id: str) -> dict | None:
    db = get_db()
    return await db.plans.find_one({"project_id": project_id}, {"_id": 0})


async def add_build(project_id: str, build: dict, repair: dict | None = None) -> dict:
    db = get_db()
    doc = {
        "project_id": project_id,
        "build": build,
        "repair": repair or {},
        "overall_status": (build or {}).get("overall_status"),
        "created_at": now(),
    }
    await db.builds.insert_one(doc)
    return {k: v for k, v in doc.items() if k != "_id"}


async def list_builds(project_id: str, limit: int = 50) -> list[dict]:
    db = get_db()
    cur = db.builds.find({"project_id": project_id}, {"_id": 0}).sort("created_at", -1).limit(limit)
    return [d async for d in cur]


async def add_acceptance(project_id: str, report: dict) -> dict:
    db = get_db()
    doc = {"project_id": project_id, "report": report, "created_at": now()}
    await db.acceptance.insert_one(doc)
    return {k: v for k, v in doc.items() if k != "_id"}


async def latest_acceptance(project_id: str) -> dict | None:
    db = get_db()
    doc = await db.acceptance.find_one({"project_id": project_id}, {"_id": 0}, sort=[("created_at", -1)])
    return doc


async def add_export(project_id: str, export: dict) -> dict:
    db = get_db()
    doc = {"project_id": project_id, "export": export, "created_at": now()}
    await db.exports.insert_one(doc)
    return {k: v for k, v in doc.items() if k != "_id"}


async def latest_export(project_id: str) -> dict | None:
    db = get_db()
    return await db.exports.find_one({"project_id": project_id}, {"_id": 0}, sort=[("created_at", -1)])


# ---------- Constraints (per-project bounded customization) ----------
async def get_constraints(project_id: str) -> dict | None:
    db = get_db()
    doc = await db.constraints.find_one({"project_id": project_id}, {"_id": 0})
    if not doc:
        return None
    return doc.get("constraints") or doc  # backward-compat


async def set_constraints(project_id: str, constraints: dict) -> dict:
    db = get_db()
    body = {
        "project_id": project_id,
        "constraints": constraints,
        "updated_at": now(),
    }
    await db.constraints.update_one(
        {"project_id": project_id}, {"$set": body}, upsert=True
    )
    return constraints


# ---------- Improve attempts ----------
async def add_improve_attempt(project_id: str, attempt: dict) -> dict:
    db = get_db()
    doc = {
        "project_id": project_id,
        "attempt_id": attempt.get("id"),
        "attempt": attempt,
        "status": attempt.get("status"),
        "created_at": attempt.get("created_at") or now(),
    }
    await db.improve_attempts.insert_one(doc)
    return {k: v for k, v in doc.items() if k != "_id"}


async def list_improve_attempts(project_id: str, limit: int = 30) -> list[dict]:
    db = get_db()
    cur = (
        db.improve_attempts.find({"project_id": project_id}, {"_id": 0})
        .sort("created_at", -1)
        .limit(limit)
    )
    return [d async for d in cur]


async def get_improve_attempt(project_id: str, attempt_id: str) -> dict | None:
    db = get_db()
    return await db.improve_attempts.find_one(
        {"project_id": project_id, "attempt_id": attempt_id}, {"_id": 0}
    )
