"""Mongo connection + collections + indexes."""
from __future__ import annotations

import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def init_client() -> tuple[AsyncIOMotorClient, AsyncIOMotorDatabase]:
    global _client, _db
    if _client is None:
        url = os.environ["MONGO_URL"]
        name = os.environ.get("DB_NAME", "local_app_creator")
        _client = AsyncIOMotorClient(url, uuidRepresentation="standard")
        _db = _client[name]
    assert _db is not None
    return _client, _db


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        init_client()
    assert _db is not None
    return _db


async def ensure_indexes() -> None:
    db = get_db()
    await db.projects.create_index("id", unique=True)
    await db.projects.create_index("updated_at")
    await db.events.create_index([("project_id", 1), ("created_at", -1)])
    await db.events.create_index("id", unique=True)
    await db.runs.create_index([("project_id", 1), ("created_at", -1)])
    await db.brds.create_index("project_id", unique=True)
    await db.architectures.create_index("project_id", unique=True)
    await db.plans.create_index("project_id", unique=True)
    await db.builds.create_index([("project_id", 1), ("created_at", -1)])
    await db.acceptance.create_index([("project_id", 1), ("created_at", -1)])
    await db.exports.create_index([("project_id", 1), ("created_at", -1)])
    await db.constraints.create_index("project_id", unique=True)
    await db.improve_attempts.create_index([("project_id", 1), ("created_at", -1)])
    await db.improve_attempts.create_index(
        [("project_id", 1), ("attempt_id", 1)], unique=True
    )


async def close_client() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None
