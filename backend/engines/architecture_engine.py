"""Architecture engine: deterministic classification with optional LLM hint.

Returns one of: frontend_only | api_driven | db_backed | backend_required | full_stack.
Blocks invalid combinations unless the caller explicitly opts into limited_prototype.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

KINDS = ("frontend_only", "api_driven", "db_backed", "backend_required", "full_stack")


@dataclass
class ArchitectureDecision:
    kind: str
    reasoning: list[str]
    requires_backend: bool
    requires_database: bool
    blocked: bool = False
    block_reasons: list[str] | None = None
    limited_prototype_accepted: bool = False
    # Indices into brd.requirements of items that depend on the missing
    # backend/persistence layer when limited_prototype frontend_only is accepted.
    # Plan/Acceptance use this to mark them as `status=unsupported` honestly.
    unsupported_requirement_indices: list[int] | None = None
    unsupported_signal_keywords: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["block_reasons"] = d["block_reasons"] or []
        d["unsupported_requirement_indices"] = d["unsupported_requirement_indices"] or []
        d["unsupported_signal_keywords"] = d["unsupported_signal_keywords"] or []
        return d


_BACKEND_KEYWORDS = {
    "persist", "database", "save", "store", "record", "history", "crud",
    "login", "signup", "auth", "user account", "upload", "file storage",
    "api", "backend", "server", "webhook", "integration", "third-party",
    "external service", "payment", "send email",
}


def _has_any(brd: dict[str, Any], keywords: list[str]) -> tuple[bool, list[str]]:
    """Search BRD requirements list / description for any of the keywords."""
    haystack = []
    text = (brd.get("description", "") or "").lower()
    haystack.append(text)
    for r in brd.get("requirements", []) or []:
        if isinstance(r, dict):
            haystack.append((r.get("text", "") + " " + r.get("detail", "")).lower())
        elif isinstance(r, str):
            haystack.append(r.lower())
    hits: list[str] = []
    for kw in keywords:
        if any(kw in h for h in haystack):
            hits.append(kw)
    return (len(hits) > 0), hits


def _backend_dependent_requirement_indices(brd: dict[str, Any]) -> tuple[list[int], list[str]]:
    """Return indices of BRD requirements whose text hits any backend keyword.

    Also returns the de-duplicated list of keywords that actually triggered the hit
    so we can record an honest reason on each marked requirement.
    """
    hit_indices: list[int] = []
    hit_keywords: set[str] = set()
    for i, r in enumerate(brd.get("requirements", []) or []):
        if isinstance(r, dict):
            text = (r.get("text", "") + " " + r.get("detail", "")).lower()
        elif isinstance(r, str):
            text = r.lower()
        else:
            continue
        local_hits = [kw for kw in _BACKEND_KEYWORDS if kw in text]
        if local_hits:
            hit_indices.append(i)
            hit_keywords.update(local_hits)
    return hit_indices, sorted(hit_keywords)


def detect_architecture(brd: dict[str, Any], allow_limited_prototype: bool = False) -> ArchitectureDecision:
    needs_persist, persist_hits = _has_any(brd, [
        "persist", "database", "save", "store", "record", "history", "crud", "login", "signup", "auth",
        "user account", "upload", "file storage",
    ])
    needs_api, api_hits = _has_any(brd, [
        "api", "backend", "server", "webhook", "integration", "third-party", "external service",
        "payment", "send email",
    ])
    needs_ui, ui_hits = _has_any(brd, [
        "ui", "page", "button", "form", "dashboard", "interface", "frontend", "react", "website",
        "web app", "chart", "table", "list",
    ])

    reasoning: list[str] = []
    if needs_ui:
        reasoning.append(f"UI signals present: {ui_hits}")
    if needs_api:
        reasoning.append(f"API/backend signals: {api_hits}")
    if needs_persist:
        reasoning.append(f"Persistence signals: {persist_hits}")

    # Decision tree
    if needs_ui and needs_persist:
        kind = "full_stack"
    elif needs_ui and needs_api:
        kind = "api_driven"
    elif needs_persist and not needs_ui:
        kind = "backend_required"
    elif needs_api and not needs_ui:
        kind = "backend_required"
    elif needs_ui and not needs_api and not needs_persist:
        kind = "frontend_only"
    else:
        # Default safe path: assume full_stack to avoid silent under-scoping.
        kind = "full_stack"
        reasoning.append("Insufficient signals; defaulting to full_stack to avoid under-scoping.")

    # Block invalid combos: e.g., user explicitly forces frontend_only but BRD demands persistence.
    blocked = False
    block_reasons: list[str] = []
    unsupported_idx: list[int] = []
    unsupported_kw: list[str] = []
    forced_kind = (brd.get("forced_architecture") or "").strip().lower()
    if forced_kind and forced_kind in KINDS:
        if forced_kind == "frontend_only" and (needs_persist or needs_api):
            if not allow_limited_prototype:
                blocked = True
                block_reasons.append(
                    "BRD requires persistence/API but forced_architecture=frontend_only. "
                    "Opt-in 'limited_prototype' to proceed knowingly."
                )
            else:
                kind = forced_kind
                # Identify the specific requirements that won't be deliverable
                # so the override flow can mark them unsupported in the BRD.
                unsupported_idx, unsupported_kw = _backend_dependent_requirement_indices(brd)
                reasoning.append(
                    "limited_prototype: user accepted frontend-only despite backend signals. "
                    f"{len(unsupported_idx)} requirement(s) will be marked unsupported."
                )
        else:
            kind = forced_kind
            reasoning.append(f"forced_architecture honored: {forced_kind}")

    return ArchitectureDecision(
        kind=kind,
        reasoning=reasoning,
        requires_backend=kind not in {"frontend_only"},
        requires_database=kind in {"full_stack", "backend_required", "db_backed"},
        blocked=blocked,
        block_reasons=block_reasons,
        limited_prototype_accepted=bool(allow_limited_prototype),
        unsupported_requirement_indices=unsupported_idx,
        unsupported_signal_keywords=unsupported_kw,
    )
