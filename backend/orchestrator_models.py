"""Pydantic models for the orchestrator (Local App Creator)."""
from __future__ import annotations

import time
import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ProjectState = Literal[
    "Idea", "BRD", "Architecture", "Plan", "Generating", "Building", "Repair", "Acceptance", "Export",
]

ALL_STATES: tuple[ProjectState, ...] = (
    "Idea", "BRD", "Architecture", "Plan", "Generating", "Building", "Repair", "Acceptance", "Export",
)


def now() -> float:
    return time.time()


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    idea: str = Field(min_length=5, max_length=4000)


class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str
    idea: str
    state: ProjectState = "Idea"
    workspace_dir: str = ""
    brd_maturity: int = 0
    last_build_status: str | None = None
    last_acceptance_status: str | None = None
    last_export_path: str | None = None
    # Phase 4: rework / ingest existing project
    ingested: bool = False
    ingest_source: str = ""   # "zip:<filename>" | "url:<https://...>"
    ingest_status: str = ""   # extracting | cloning | deriving | complete | complete_with_warning | failed
    ingest_error: str = ""
    created_at: float = Field(default_factory=now)
    updated_at: float = Field(default_factory=now)


class AnswerSubmission(BaseModel):
    question_id: str
    question: str
    answer: str = Field(min_length=1)


class BRDRecord(BaseModel):
    project_id: str
    questions: list[dict[str, Any]] = Field(default_factory=list)
    answers: list[AnswerSubmission] = Field(default_factory=list)
    brd: dict[str, Any] = Field(default_factory=dict)
    maturity: int = 0
    updated_at: float = Field(default_factory=now)


class ArchitectureOverrideRequest(BaseModel):
    forced_architecture: str | None = None
    allow_limited_prototype: bool = False


class GenerateRequest(BaseModel):
    pass


class EventRecord(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    project_id: str
    type: str
    actor: str = "system"
    payload: dict[str, Any] = Field(default_factory=dict)
    message: str = ""
    severity: Literal["info", "warning", "error", "success"] = "info"
    created_at: float = Field(default_factory=now)
