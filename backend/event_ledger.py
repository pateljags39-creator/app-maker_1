"""In-process pub/sub for SSE. Persists events to Mongo and broadcasts to listeners."""
from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from typing import AsyncIterator

from orchestrator_models import EventRecord
from db import get_db

logger = logging.getLogger("event_ledger")


class EventLedger:
    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue]] = defaultdict(set)

    async def emit(self, event: EventRecord) -> None:
        # Persist
        db = get_db()
        await db.events.insert_one(event.model_dump())
        # Broadcast (per project + global)
        payload = event.model_dump()
        for key in (event.project_id, "*"):
            for q in list(self._subscribers.get(key, set())):
                try:
                    q.put_nowait(payload)
                except asyncio.QueueFull:
                    pass

    async def emit_simple(self, project_id: str, type: str, message: str = "",
                          payload: dict | None = None, actor: str = "system",
                          severity: str = "info") -> EventRecord:
        rec = EventRecord(
            project_id=project_id, type=type, actor=actor, message=message,
            payload=payload or {}, severity=severity,  # type: ignore[arg-type]
        )
        await self.emit(rec)
        return rec

    async def subscribe(self, project_id: str | None = None) -> AsyncIterator[dict]:
        """Yields event dicts as they arrive. Project_id=None subscribes to all."""
        key = project_id or "*"
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        self._subscribers[key].add(q)
        try:
            while True:
                payload = await q.get()
                yield payload
        finally:
            self._subscribers[key].discard(q)

    async def list(self, project_id: str, limit: int = 100, before: float | None = None) -> list[dict]:
        db = get_db()
        q: dict = {"project_id": project_id}
        if before is not None:
            q["created_at"] = {"$lt": before}
        cursor = db.events.find(q, {"_id": 0}).sort("created_at", -1).limit(limit)
        return [doc async for doc in cursor]


# Singleton accessor
_ledger: EventLedger | None = None


def get_ledger() -> EventLedger:
    global _ledger
    if _ledger is None:
        _ledger = EventLedger()
    return _ledger


def sse_pack(data: dict, event: str | None = None) -> bytes:
    """Encode an event for the SSE wire format."""
    lines = []
    if event:
        lines.append(f"event: {event}")
    lines.append(f"data: {json.dumps(data)}")
    return ("\n".join(lines) + "\n\n").encode("utf-8")
