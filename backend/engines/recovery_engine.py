"""Recovery engine: detect & unblock projects whose background pipeline died.

When the backend restarts (hot reload, crash, deployment), any in-flight
asyncio task running `_run_pipeline` / `_do_build` / `_derive_brd_background`
is killed. The corresponding project is left frozen at `state ∈ {Generating,
Building, Repair, Acceptance}` with no error ever emitted — the user just
sees the cockpit "stuck" with no progress.

This module fixes that:

1. `sweep_stale_pipelines()` is called once on FastAPI startup. It finds every
   project in a transient state whose `updated_at` is older than a grace
   period (default 90s), records a `pipeline.aborted` ledger event, and
   resets the state back to a safe checkpoint so the user can retry.

2. `manual_recover(project_id)` does the same for one project on demand
   (exposed via POST /api/projects/{id}/recover).

The reset target is the safest prior checkpoint we can detect from existing
records:
  - has builds   -> "Acceptance" lost  -> reset to "Building"
  - has plan     -> "Generating/Building" lost -> reset to "Plan"
  - has arch     -> reset to "Architecture"
  - has brd      -> reset to "BRD"
  - else         -> "Idea"
"""
from __future__ import annotations

import logging
import time
from typing import Any

from event_ledger import get_ledger
import repositories as repo

logger = logging.getLogger("engines.recovery_engine")

TRANSIENT_STATES = {"Generating", "Building", "Repair", "Acceptance"}
DEFAULT_GRACE_SECONDS = 90.0


async def _pick_recovery_state(project_id: str) -> str:
    """Pick the safest state to revert to based on what's already persisted."""
    builds = await repo.list_builds(project_id, limit=1)
    if builds:
        return "Acceptance"  # build exists, user only lost the acceptance step
    plan = await repo.get_plan(project_id)
    if plan and (plan.get("plan") or {}).get("files"):
        return "Plan"
    arch = await repo.get_architecture(project_id)
    if arch and (arch.get("decision") or {}).get("kind"):
        return "Architecture"
    brd = await repo.get_brd(project_id)
    if brd and (brd.get("brd") or {}).get("requirements"):
        return "BRD"
    return "Idea"


async def _abort_one(proj: dict[str, Any], reason: str) -> dict[str, Any]:
    """Mark a single project as aborted + reset to safe state."""
    project_id = proj["id"]
    prev_state = proj.get("state")
    new_state = await _pick_recovery_state(project_id)
    await repo.update_project(
        project_id,
        state=new_state,
        last_build_status=proj.get("last_build_status") or "ABORTED",
    )
    await get_ledger().emit_simple(
        project_id=project_id,
        type="pipeline.aborted",
        message=(
            f"Pipeline aborted while in {prev_state} (likely server restart "
            f"or crash). State reset to {new_state}. You can retry now."
        ),
        payload={
            "previous_state": prev_state,
            "recovered_state": new_state,
            "reason": reason,
        },
        severity="warning",
    )
    return {
        "project_id": project_id,
        "previous_state": prev_state,
        "recovered_state": new_state,
        "reason": reason,
    }


async def sweep_stale_pipelines(grace_seconds: float = DEFAULT_GRACE_SECONDS) -> list[dict[str, Any]]:
    """Run on backend startup. Returns the list of recovered projects."""
    from db import get_db
    db = get_db()
    cutoff = time.time() - grace_seconds
    cursor = db.projects.find(
        {
            "state": {"$in": list(TRANSIENT_STATES)},
            "updated_at": {"$lt": cutoff},
        },
        {"_id": 0},
    )
    rows = await cursor.to_list(200)
    out: list[dict[str, Any]] = []
    for proj in rows:
        try:
            rec = await _abort_one(proj, reason="startup_sweep")
            out.append(rec)
            logger.warning(
                "Recovered stale project %s: %s -> %s",
                proj["id"], proj.get("state"), rec["recovered_state"],
            )
        except Exception as e:  # pragma: no cover
            logger.exception("Recovery failed for %s: %s", proj["id"], e)
    return out


async def manual_recover(project_id: str) -> dict[str, Any] | None:
    """User-triggered recovery for one project."""
    proj = await repo.get_project(project_id)
    if not proj:
        return None
    if proj.get("state") not in TRANSIENT_STATES:
        return {
            "project_id": project_id,
            "previous_state": proj.get("state"),
            "recovered_state": proj.get("state"),
            "reason": "no_op_not_stuck",
        }
    return await _abort_one(proj, reason="manual_recover")
