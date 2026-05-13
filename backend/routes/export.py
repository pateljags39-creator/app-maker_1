"""Routes: export ZIP + download."""
from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from engines.export_engine import export_project
from event_ledger import get_ledger
import repositories as repo

router = APIRouter(prefix="/projects/{project_id}/export", tags=["export"])


@router.post("")
async def make_export(project_id: str):
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(404, "project_not_found")
    ws = Path(proj["workspace_dir"])
    if not ws.exists():
        raise HTTPException(400, "workspace_missing")
    exp = export_project(ws, project_name=(proj.get("name") or project_id).strip() or project_id)
    rec = {
        "path": exp.path, "sha256": exp.sha256, "files": exp.files,
        "size_bytes": exp.size_bytes, "secret_findings": exp.secret_findings,
        "manifest_path": exp.manifest_path, "created_at": exp.created_at,
    }
    await repo.add_export(project_id, rec)
    await repo.update_project(project_id, last_export_path=exp.path)
    await get_ledger().emit_simple(
        project_id=project_id, type="export.completed",
        message=f"Exported {Path(exp.path).name}",
        payload={"files": exp.files, "size_bytes": exp.size_bytes, "secrets": exp.secret_findings},
        severity="success",
    )
    return rec


@router.get("")
async def latest_export(project_id: str):
    doc = await repo.latest_export(project_id)
    if not doc:
        return {"project_id": project_id, "export": None}
    return doc


@router.get("/download")
async def download(project_id: str):
    doc = await repo.latest_export(project_id)
    if not doc:
        raise HTTPException(404, "no_export_yet")
    p = Path(doc["export"]["path"])
    if not p.exists():
        raise HTTPException(404, "export_file_missing")
    return FileResponse(path=str(p), filename=p.name, media_type="application/zip")


@router.get("/manifest")
async def manifest(project_id: str):
    doc = await repo.latest_export(project_id)
    if not doc:
        raise HTTPException(404, "no_export_yet")
    mp = Path(doc["export"]["manifest_path"])
    if not mp.exists():
        raise HTTPException(404, "manifest_missing")
    import json
    return json.loads(mp.read_text("utf-8"))
