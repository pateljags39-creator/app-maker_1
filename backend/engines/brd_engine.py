"""BRD engine: SME questions, requirement extraction, maturity scoring, missing-info detection."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from .llm_gateway import LLMGateway, LLMError

logger = logging.getLogger("engines.brd_engine")

SME_SYSTEM = """You are a senior business analyst and software architect.
You are talking to a product owner who described an app idea. Your job is to elicit
the MINIMUM set of high-yield, SME-style clarifying questions that close the largest
gaps in the BRD.

Return STRICT JSON:
{
  "questions": [
    {"id":"q1", "category":"users"|"data"|"workflows"|"non_functional"|"integrations"|"ui"|"constraints",
     "text":"...", "why_it_matters":"...",
     "answer_kind":"short_text"|"long_text"|"single_choice"|"multi_choice"|"yes_no"|"number",
     "choices": ["..."]  /* only if answer_kind in single_choice|multi_choice */ }
  ]
}

Rules: 4-7 questions max. No yes/no chains. Each question should unlock multiple BRD slots.
Prefer questions about: user roles, data entities, persistence, key workflows, integrations,
non-functional needs (offline? auth? perf?), and explicit UI surfaces required.
"""

BRD_SYSTEM = """You are turning a free-form product idea + Q&A pairs into a structured BRD.
Return STRICT JSON:
{
  "app_name": "...",
  "description": "...",
  "users": [{"role":"...","goals":["..."]}],
  "entities": [{"name":"Note","fields":[{"name":"id","type":"int"}]}],
  "requirements": [
    {"id":"R1","text":"...","category":"functional"|"non_functional"|"data"|"ui"|"integration",
     "status":"supported"|"partial"|"unsupported"|"blocked",
     "reason":"<short>"}
  ],
  "workflows": [{"name":"...","steps":["..."]}],
  "integrations": [],
  "non_functional": {"auth": false, "offline": false, "realtime": false},
  "maturity": {"score": 0-100, "missing": ["..."], "notes":"..."}
}

Rules:
- Mark requirements honestly: 'supported' if our default stack (React+Vite + FastAPI + SQLite) can do it.
- Use 'partial' if it requires extra steps; 'unsupported' if our stack/scope can't deliver; 'blocked' for conflicts.
- Score maturity 0-100; higher = more complete. List concretely what's missing.
"""


@dataclass
class BRDQuestion:
    id: str
    text: str
    category: str
    why_it_matters: str = ""
    answer_kind: str = "long_text"
    choices: list[str] = field(default_factory=list)


async def generate_questions(gateway: LLMGateway, idea: str, prior: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    user = (
        f"# Product idea\n{idea.strip()}\n\n"
        f"# Prior BRD (may be empty)\n```json\n{json.dumps(prior or {}, indent=2)}\n```\n\n"
        "Return STRICT JSON: {\"questions\": [...]}."
    )
    resp = await gateway.complete(
        system=SME_SYSTEM, user=user, json_mode=True,
        temperature=0.3, max_output_tokens=6000,
    )
    data = resp.as_json()
    qs = data.get("questions", []) if isinstance(data, dict) else []
    return qs


async def derive_brd(
    gateway: LLMGateway,
    idea: str,
    qa_pairs: list[dict[str, Any]],
    prior: dict[str, Any] | None = None,
) -> dict[str, Any]:
    user = (
        f"# Product idea\n{idea.strip()}\n\n"
        f"# Q&A pairs\n```json\n{json.dumps(qa_pairs, indent=2)}\n```\n\n"
        f"# Prior BRD (merge)\n```json\n{json.dumps(prior or {}, indent=2)}\n```\n\n"
        "Return the BRD JSON as specified."
    )
    resp = await gateway.complete(
        system=BRD_SYSTEM, user=user, json_mode=True,
        temperature=0.15, max_output_tokens=5000,
    )
    brd = resp.as_json()
    if not isinstance(brd, dict):
        raise LLMError("BRD shape invalid")
    return brd
