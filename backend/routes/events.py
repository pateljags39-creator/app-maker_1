"""Routes: event ledger (paged + SSE stream)."""
from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from event_ledger import get_ledger
import repositories as repo

router = APIRouter(prefix="/projects/{project_id}/events", tags=["events"])


@router.get("")
async def list_events(project_id: str, limit: int = Query(50, le=200), before: float | None = None):
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(404, "project_not_found")
    return await get_ledger().list(project_id, limit=limit, before=before)


def _sse_format(event: str, data: dict) -> bytes:
    payload = json.dumps(data, default=str)
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")


@router.get("/stream")
async def stream(project_id: str):
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(404, "project_not_found")
    led = get_ledger()

    async def gen() -> AsyncIterator[bytes]:
        yield _sse_format("hello", {"project_id": project_id})
        try:
            async for evt in led.subscribe(project_id):
                yield _sse_format("event", evt)
        except asyncio.CancelledError:
            return

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
