"""Routes: list and read generated files."""
from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

import repositories as repo

router = APIRouter(prefix="/projects/{project_id}/files", tags=["files"])

EXCLUDE = {"node_modules", ".factory", "__pycache__", ".git", "dist", "build", ".venv"}
TEXT_EXTS = {".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".html", ".css", ".md", ".txt",
             ".yml", ".yaml", ".toml", ".ini", ".sh"}


@router.get("")
async def list_files(project_id: str):
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(404, "project_not_found")
    ws = Path(proj["workspace_dir"])
    out = []
    if ws.exists():
        for p in sorted(ws.rglob("*")):
            rel = p.relative_to(ws)
            if set(rel.parts) & EXCLUDE:
                continue
            if p.is_file():
                out.append({
                    "path": rel.as_posix(),
                    "size": p.stat().st_size,
                    "kind": "file",
                })
            elif p.is_dir():
                out.append({"path": rel.as_posix() + "/", "size": 0, "kind": "dir"})
    return {"workspace": str(ws), "files": out}


@router.get("/content", response_class=PlainTextResponse)
async def get_file_content(project_id: str, path: str = Query(...)):
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(404, "project_not_found")
    ws = Path(proj["workspace_dir"]).resolve()
    p = (ws / path).resolve()
    if not str(p).startswith(str(ws)):
        raise HTTPException(400, "unsafe_path")
    if not p.exists() or not p.is_file():
        raise HTTPException(404, "file_not_found")
    if p.suffix.lower() not in TEXT_EXTS and p.stat().st_size > 200_000:
        raise HTTPException(415, "binary_or_too_large")
    return p.read_text("utf-8", "replace")
