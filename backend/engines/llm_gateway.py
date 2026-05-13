"""LLM Gateway: Direct Gemini API (primary) -> Emergent Universal LLM Key (fallback).

Design notes:
- Never logs API keys.
- Detects quota / 429 / RESOURCE_EXHAUSTED errors and falls back automatically.
- Returns identical interface for both providers (sync wrappers using asyncio).
- Supports plain text and structured JSON responses.
- Tracks which provider answered (for ops visibility) without leaking secrets.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import uuid
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("engines.llm_gateway")

# ---------- Provider availability ----------
try:
    from google import genai as google_genai
    from google.genai import types as google_genai_types
    _HAS_DIRECT_GEMINI = True
except Exception:  # pragma: no cover
    _HAS_DIRECT_GEMINI = False

try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    _HAS_EMERGENT = True
except Exception:  # pragma: no cover
    _HAS_EMERGENT = False


# ---------- Error types ----------
class LLMError(RuntimeError):
    pass


class QuotaExhaustedError(LLMError):
    """Raised when a provider hits quota / rate-limit; gateway will fall back."""


class AllProvidersExhaustedError(LLMError):
    """Raised when BOTH primary and fallback are unavailable."""


@dataclass
class LLMResponse:
    text: str
    provider: str  # "gemini_direct" | "emergent_gemini"
    model: str
    tokens: dict[str, int] = field(default_factory=dict)

    def as_json(self) -> Any:
        """Parse text as JSON. Tries to extract a fenced block if needed.
        Also attempts to recover from truncated outputs by trimming to the last
        complete JSON object/array marker.
        """
        raw = self.text.strip()
        # Strip code fences if present (LLMs sometimes wrap JSON in ```json ... ```).
        fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", raw, re.DOTALL)
        if fence:
            raw = fence.group(1).strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            # Last-resort: extract the largest JSON-looking substring.
            match = re.search(r"(\{.*\}|\[.*\])", raw, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            # Try to truncate to the last balanced bracket and retry.
            recovered = _try_recover_truncated_json(raw)
            if recovered is not None:
                return recovered
            raise LLMError(f"LLM did not return valid JSON: {e}; head={raw[:200]!r}") from e


def _try_recover_truncated_json(raw: str) -> Any | None:
    """Heuristic: if JSON looks truncated, walk back from the end to the last
    point where brackets and quotes balance, then try to parse."""
    if not raw:
        return None
    # Find start
    start = raw.find("{")
    if start < 0:
        start = raw.find("[")
    if start < 0:
        return None
    s = raw[start:]
    # Walk backward from end, attempting to close open braces.
    in_string = False
    escape = False
    stack: list[str] = []
    pairs = {"{": "}", "[": "]"}
    last_safe = -1
    for i, ch in enumerate(s):
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in pairs:
            stack.append(pairs[ch])
        elif stack and ch == stack[-1]:
            stack.pop()
            if not stack:
                last_safe = i  # complete top-level value ended here
    if last_safe >= 0:
        try:
            return json.loads(s[: last_safe + 1])
        except json.JSONDecodeError:
            pass
    # If we're in a string, try truncating to before the open quote of that string.
    if in_string:
        # Find last unescaped quote
        for j in range(len(s) - 1, -1, -1):
            if s[j] == '"' and (j == 0 or s[j - 1] != "\\"):
                trimmed = s[:j]
                # Now close any open arrays/objects.
                closing = []
                in_str = False
                esc = False
                stk: list[str] = []
                for ch in trimmed:
                    if esc:
                        esc = False
                        continue
                    if ch == "\\":
                        esc = True
                        continue
                    if ch == '"':
                        in_str = not in_str
                        continue
                    if in_str:
                        continue
                    if ch in pairs:
                        stk.append(pairs[ch])
                    elif stk and ch == stk[-1]:
                        stk.pop()
                # Remove trailing comma if any
                trimmed = trimmed.rstrip().rstrip(",").rstrip()
                # If we ended inside a key:value before string value, strip the dangling `"key":`
                trimmed = re.sub(r",\s*\"[^\"]*\"\s*:\s*$", "", trimmed)
                trimmed = re.sub(r"\{\s*\"[^\"]*\"\s*:\s*$", "{", trimmed)
                while stk:
                    closing.append(stk.pop())
                candidate = trimmed + "".join(closing)
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue
    return None


# ---------- Model tier routing ----------
# The user explicitly asked: "use flash for small fixes and 2.5 pro for major
# tasks. Try to do in less calls as there is rate per min limit."
#
# Light  = high-volume, narrow-scope calls (BRD questions, per-file generation,
#          architecture classification hints, repair triage).
# Heavy  = single-shot, holistic reasoning (BRD derive, full project plan,
#          repair patch synthesis).
#
# Per-call override is supported via complete(..., tier=..., model=...).
TIER_MODELS: dict[str, str] = {
    "light": "gemini-2.5-flash",
    "heavy": "gemini-2.5-pro",
}
DEFAULT_TIER = "light"


# ---------- Gateway ----------
class LLMGateway:
    """Primary direct-Gemini, fallback Emergent universal key.

    Supports a `tier` parameter on each call so that holistic / high-stakes
    reasoning steps (plan, BRD derive, repair synthesis) are routed to
    gemini-2.5-pro while high-volume small-scope steps stay on
    gemini-2.5-flash (cheaper, higher RPM).
    """

    def __init__(
        self,
        gemini_api_key: str | None = None,
        emergent_key: str | None = None,
        model: str = "gemini-2.5-flash",
    ) -> None:
        self.gemini_api_key = gemini_api_key or os.environ.get("GEMINI_API_KEY")
        self.emergent_key = emergent_key or os.environ.get("EMERGENT_LLM_KEY")
        self.model = model
        self._direct_client: Any | None = None
        self._primary_disabled = False  # set once direct primary throws quota; sticks for session

        if _HAS_DIRECT_GEMINI and self.gemini_api_key:
            try:
                self._direct_client = google_genai.Client(api_key=self.gemini_api_key)
            except Exception as e:  # pragma: no cover
                logger.warning("Direct Gemini client init failed: %s", type(e).__name__)
                self._direct_client = None

        if not (self._direct_client or (self.emergent_key and _HAS_EMERGENT)):
            raise AllProvidersExhaustedError(
                "No LLM provider available: configure GEMINI_API_KEY and/or EMERGENT_LLM_KEY."
            )

    def _resolve_model(self, tier: str | None, model: str | None) -> str:
        """Pick the effective model for this call.
        Explicit `model=` wins, then `tier=`, else the default constructor model."""
        if model:
            return model
        if tier and tier in TIER_MODELS:
            return TIER_MODELS[tier]
        return self.model

    # --- public ---
    async def complete(
        self,
        system: str,
        user: str,
        *,
        json_mode: bool = False,
        temperature: float = 0.2,
        max_output_tokens: int = 8192,
        tier: str | None = None,
        model: str | None = None,
    ) -> LLMResponse:
        """Try primary, fall back on quota/auth/quota errors.

        Per-call routing:
            tier="light"  -> gemini-2.5-flash (default)
            tier="heavy"  -> gemini-2.5-pro
        `model=` overrides both.
        """
        effective_model = self._resolve_model(tier, model)
        # Try direct Gemini first if available and not previously disabled
        if self._direct_client and not self._primary_disabled:
            try:
                return await self._complete_direct(
                    system, user,
                    json_mode=json_mode,
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                    model_override=effective_model,
                )
            except QuotaExhaustedError as e:
                logger.warning("Primary Gemini quota exhausted, switching to fallback. Reason=%s", str(e)[:120])
                self._primary_disabled = True
            except LLMError as e:
                logger.warning("Primary Gemini error, switching to fallback. Reason=%s", str(e)[:120])
                # We don't permanently disable here; transient errors may recover.

        # Fallback: Emergent
        if self.emergent_key and _HAS_EMERGENT:
            return await self._complete_emergent(
                system, user,
                json_mode=json_mode,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                model_override=effective_model,
            )

        raise AllProvidersExhaustedError(
            "Primary Gemini failed and no Emergent fallback configured (set EMERGENT_LLM_KEY)."
        )

    # --- providers ---
    async def _complete_direct(
        self,
        system: str,
        user: str,
        *,
        json_mode: bool,
        temperature: float,
        max_output_tokens: int,
        model_override: str | None = None,
    ) -> LLMResponse:
        assert self._direct_client is not None
        effective_model = model_override or self.model
        cfg_kwargs: dict[str, Any] = {
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
            "system_instruction": system,
        }
        if json_mode:
            cfg_kwargs["response_mime_type"] = "application/json"

        def _call() -> Any:
            return self._direct_client.models.generate_content(
                model=effective_model,
                contents=user,
                config=google_genai_types.GenerateContentConfig(**cfg_kwargs),
            )

        try:
            resp = await asyncio.to_thread(_call)
        except Exception as e:
            msg = str(e)
            low = msg.lower()
            if any(k in low for k in ("resource_exhausted", "quota", "rate limit", "429")):
                raise QuotaExhaustedError(msg) from e
            if any(k in low for k in ("invalid api key", "api key not valid", "unauthorized", "403")):
                # Treat as quota-exhausted so we fall back permanently.
                raise QuotaExhaustedError(f"auth_error: {msg}") from e
            raise LLMError(f"gemini_direct_error: {type(e).__name__}") from e

        text = getattr(resp, "text", None) or ""
        if not text and getattr(resp, "candidates", None):
            try:
                parts = resp.candidates[0].content.parts
                text = "".join(getattr(p, "text", "") or "" for p in parts)
            except Exception:
                pass
        if not text:
            raise LLMError("gemini_direct empty response")

        usage = getattr(resp, "usage_metadata", None)
        tokens = {}
        if usage is not None:
            tokens = {
                "prompt": int(getattr(usage, "prompt_token_count", 0) or 0),
                "output": int(getattr(usage, "candidates_token_count", 0) or 0),
            }

        return LLMResponse(text=text, provider="gemini_direct", model=effective_model, tokens=tokens)

    async def _complete_emergent(
        self,
        system: str,
        user: str,
        *,
        json_mode: bool,
        temperature: float,
        max_output_tokens: int,
        model_override: str | None = None,
    ) -> LLMResponse:
        effective_model = model_override or self.model
        # emergentintegrations chat: stateful, but we use fresh session per call to keep stateless behaviour.
        sysmsg = system
        if json_mode:
            sysmsg = (
                system
                + "\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown fences. No commentary."
            )
        chat = LlmChat(
            api_key=self.emergent_key,
            session_id=f"lac-{uuid.uuid4().hex[:12]}",
            system_message=sysmsg,
        ).with_model("gemini", effective_model)
        msg = UserMessage(text=user)
        try:
            text = await chat.send_message(msg)
        except Exception as e:
            msg_l = str(e).lower()
            if any(k in msg_l for k in ("resource_exhausted", "quota", "rate limit", "429")):
                raise QuotaExhaustedError(str(e)) from e
            raise LLMError(f"emergent_gemini_error: {type(e).__name__}") from e
        if not text:
            raise LLMError("emergent_gemini empty response")
        return LLMResponse(text=text, provider="emergent_gemini", model=effective_model)

    # --- introspection (safe, no secrets) ---
    def status(self) -> dict[str, Any]:
        return {
            "primary_available": bool(self._direct_client) and not self._primary_disabled,
            "primary_disabled_quota": self._primary_disabled,
            "fallback_available": bool(self.emergent_key and _HAS_EMERGENT),
            "model": self.model,
            "tier_models": dict(TIER_MODELS),
            "default_tier": DEFAULT_TIER,
        }
