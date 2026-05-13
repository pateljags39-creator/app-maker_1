"""Routes: project CRUD and lifecycle."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pathlib import Path
import os

from event_ledger import get_ledger
from orchestrator_models import Project, ProjectCreate
import repositories as repo

router = APIRouter(prefix="/projects", tags=["projects"])

WORKSPACE_DIR = Path(os.environ.get("WORKSPACE_DIR", "/app/workspace")) / "projects"


@router.get("")
async def list_projects():
    return await repo.list_projects()


@router.post("", status_code=201)
async def create_project(payload: ProjectCreate):
    proj = Project(name=payload.name, idea=payload.idea)
    proj.workspace_dir = str(WORKSPACE_DIR / proj.id)
    Path(proj.workspace_dir).mkdir(parents=True, exist_ok=True)
    doc = await repo.create_project(proj)
    await get_ledger().emit_simple(
        project_id=proj.id, type="project.created",
        message=f"Project '{proj.name}' created",
        payload={"name": proj.name}, severity="success",
    )
    return doc


@router.get("/{project_id}")
async def get_project(project_id: str):
    doc = await repo.get_project(project_id)
    if not doc:
        raise HTTPException(404, "project_not_found")
    return doc


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str):
    n = await repo.delete_project(project_id)
    if n == 0:
        raise HTTPException(404, "project_not_found")
    return None
