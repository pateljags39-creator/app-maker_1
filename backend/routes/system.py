"""Routes: system health (LLM provider status)."""
from __future__ import annotations

from fastapi import APIRouter
from engines.llm_gateway import LLMGateway

router = APIRouter(prefix="/system", tags=["system"])

_gateway: LLMGateway | None = None


def _gw() -> LLMGateway:
    global _gateway
    if _gateway is None:
        _gateway = LLMGateway()
    return _gateway


@router.get("/health")
async def health():
    gw = _gw()
    s = gw.status()
    s["version"] = "0.2.0"
    s["product"] = "Local App Creator"
    return s
