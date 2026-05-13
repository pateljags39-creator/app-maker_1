"""State machine for project lifecycle. Enforces valid transitions."""
from __future__ import annotations

from typing import Set

from orchestrator_models import ALL_STATES, ProjectState

# Allowed forward transitions. Going "back" is allowed only to BRD/Architecture/Plan for re-edit.
FORWARD: dict[ProjectState, Set[ProjectState]] = {
    "Idea":        {"BRD"},
    "BRD":         {"BRD", "Architecture"},
    "Architecture":{"Architecture", "Plan", "BRD"},
    "Plan":        {"Plan", "Generating", "Architecture"},
    "Generating":  {"Generating", "Building", "Plan"},
    "Building":    {"Building", "Repair", "Acceptance"},
    "Repair":      {"Repair", "Building", "Acceptance"},
    "Acceptance":  {"Acceptance", "Export", "Plan", "Building"},
    "Export":      {"Export", "Plan", "BRD"},
}


def can_transition(from_state: ProjectState, to_state: ProjectState) -> bool:
    if to_state not in ALL_STATES:
        return False
    return to_state in FORWARD.get(from_state, set())


def next_advisable(state: ProjectState) -> list[ProjectState]:
    return sorted(FORWARD.get(state, set()))
