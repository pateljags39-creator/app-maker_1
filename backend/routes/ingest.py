"""Routes: ingest an existing project from a ZIP upload or a public git URL."""
from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from engines.ingest_engine import (
    MAX_ZIP_BYTES,
    clone_git_url,
    ingest_to_project,
    safe_extract_zip,
    validate_git_url,
)
from engines.llm_gateway import LLMGateway
from event_ledger import get_ledger
from orchestrator_models import Project
import repositories as repo

logger = logging.getLogger("routes.ingest")
router = APIRouter(prefix="/projects/ingest", tags=["ingest"])

WORKSPACE_DIR = Path(os.environ.get("WORKSPACE_DIR", "/app/workspace")) / "projects"


class IngestUrlRequest(BaseModel):
    url: str = Field(..., min_length=8, max_length=512)
    name: str = Field("", max_length=120)


# ---------- shared background task ----------
async def _derive_brd_background(project_id: str, source_info: str) -> None:
    led = get_ledger()
    proj = await repo.get_project(project_id)
    if not proj:
        return
    ws = Path(proj["workspace_dir"])
    await led.emit_simple(
        project_id, "ingest.deriving",
        "Inferring BRD from code (1 Pro call)", severity="info",
    )
    try:
        gw = LLMGateway()
        result = await ingest_to_project(ws, source_info, gw)
    except Exception as e:
        logger.exception("ingest pipeline crashed for %s", project_id)
        await repo.update_project(
            project_id, ingest_status="failed",
            ingest_error=f"{type(e).__name__}: {str(e)[:240]}",
            state="Idea",
        )
        await led.emit_simple(
            project_id, "ingest.failed",
            f"Ingest failed: {type(e).__name__}", severity="error",
        )
        return

    # Persist BRD, architecture, synthesized plan.
    await repo.upsert_brd(
        project_id,
        questions=[], answers=[],
        brd=result["brd"],
        maturity=int(result["brd"].get("maturity_estimate", 50) or 50),
    )
    await repo.upsert_architecture(project_id, result["architecture"])
    await repo.upsert_plan(project_id, result["plan"])
    await repo.update_project(
        project_id,
        ingest_status=("complete" if not result.get("error") else "complete_with_warning"),
        ingest_error=result.get("error", "") or "",
        state="Architecture",
        brd_maturity=int(result["brd"].get("maturity_estimate", 50) or 50),
        last_build_status="UNKNOWN",  # unblocks Improve UI; user can build to refresh
    )
    sev = "success" if not result.get("error") else "warning"
    await led.emit_simple(
        project_id, "ingest.complete",
        f"Ingest complete · architecture={result['architecture']['kind']}",
        payload={
            "stack": result["stack"],
            "warnings": result.get("warnings", []),
            "endpoints": len(result["plan"].get("endpoints", [])),
            "files": len(result["plan"].get("files", [])),
        },
        severity=sev,
    )


# ---------- ZIP ingest ----------
@router.post("/zip", status_code=201)
async def ingest_zip(
    file: UploadFile = File(...),
    name: str = Form(""),
):
    if file.size is not None and file.size > MAX_ZIP_BYTES:
        raise HTTPException(413, f"file too large: max {MAX_ZIP_BYTES // 1024 // 1024} MB")
    if file.filename and not file.filename.lower().endswith(".zip"):
        raise HTTPException(400, "only .zip files are accepted")

    derived_name = (name or "").strip()
    if not derived_name:
        base = (file.filename or "Imported project")
        if base.lower().endswith(".zip"):
            base = base[:-4]
        derived_name = base[:120] or "Imported project"

    proj = Project(
        name=derived_name,
        idea=f"Imported from ZIP: {file.filename or 'upload.zip'}",
        ingested=True,
        ingest_source=f"zip:{file.filename or 'upload.zip'}",
        ingest_status="extracting",
    )
    proj.workspace_dir = str(WORKSPACE_DIR / proj.id)
    Path(proj.workspace_dir).mkdir(parents=True, exist_ok=True)
    await repo.create_project(proj)
    led = get_ledger()
    await led.emit_simple(
        proj.id, "project.created",
        f"Project '{proj.name}' created from ZIP",
        payload={"source": proj.ingest_source}, severity="success",
    )

    # Stream upload to disk with hard size cap.
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
            tmp_path = Path(tmp.name)
            total = 0
            while True:
                chunk = await file.read(1024 * 256)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_ZIP_BYTES:
                    raise HTTPException(413, "upload exceeded max size")
                tmp.write(chunk)
        # Extract in a worker thread (zipfile is sync).
        summary = await asyncio.to_thread(
            safe_extract_zip, tmp_path, Path(proj.workspace_dir)
        )
    except HTTPException:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        await repo.update_project(
            proj.id, ingest_status="failed", ingest_error="upload_too_large",
        )
        raise
    except Exception as e:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        await repo.update_project(
            proj.id, ingest_status="failed",
            ingest_error=f"zip_extract_failed: {str(e)[:200]}",
        )
        await led.emit_simple(
            proj.id, "ingest.failed",
            f"Zip extract failed: {e}", severity="error",
        )
        raise HTTPException(400, f"zip_extract_failed: {e}")
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)

    await led.emit_simple(
        proj.id, "ingest.extracted",
        f"Extracted {summary.files_imported} files ({summary.bytes_imported // 1024} KB)",
        payload={"warnings": summary.warnings[:8]}, severity="info",
    )
    await repo.update_project(proj.id, ingest_status="deriving")

    # Async BRD derivation (1 Pro call).
    asyncio.create_task(_derive_brd_background(proj.id, f"zip:{file.filename or 'upload.zip'}"))
    return await repo.get_project(proj.id)


# ---------- URL ingest ----------
@router.post("/url", status_code=201)
async def ingest_url(payload: IngestUrlRequest):
    try:
        safe_url = validate_git_url(payload.url)
    except ValueError as e:
        raise HTTPException(400, str(e))

    derived_name = (payload.name or "").strip()
    if not derived_name:
        tail = safe_url.rstrip("/").rsplit("/", 1)[-1]
        if tail.endswith(".git"):
            tail = tail[:-4]
        derived_name = (tail or "Imported project")[:120]

    proj = Project(
        name=derived_name,
        idea=f"Imported from URL: {safe_url}",
        ingested=True,
        ingest_source=f"url:{safe_url}",
        ingest_status="cloning",
    )
    proj.workspace_dir = str(WORKSPACE_DIR / proj.id)
    Path(proj.workspace_dir).mkdir(parents=True, exist_ok=True)
    await repo.create_project(proj)
    led = get_ledger()
    await led.emit_simple(
        proj.id, "project.created",
        f"Project '{proj.name}' created from URL",
        payload={"source": proj.ingest_source}, severity="success",
    )

    try:
        summary = await asyncio.to_thread(
            clone_git_url, safe_url, Path(proj.workspace_dir),
        )
    except Exception as e:
        await repo.update_project(
            proj.id, ingest_status="failed",
            ingest_error=f"git_clone_failed: {str(e)[:200]}",
        )
        await led.emit_simple(
            proj.id, "ingest.failed",
            f"Git clone failed: {e}", severity="error",
        )
        raise HTTPException(400, f"git_clone_failed: {e}")

    await led.emit_simple(
        proj.id, "ingest.cloned",
        f"Cloned {summary.files_imported} files ({summary.bytes_imported // 1024} KB)",
        payload={"warnings": summary.warnings[:8]}, severity="info",
    )
    await repo.update_project(proj.id, ingest_status="deriving")

    asyncio.create_task(_derive_brd_background(proj.id, f"url:{safe_url}"))
    return await repo.get_project(proj.id)


# ---------- status poll ----------
@router.get("/{project_id}/status")
async def ingest_status(project_id: str):
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(404, "project_not_found")
    return {
        "project_id": project_id,
        "ingested": bool(proj.get("ingested")),
        "ingest_status": proj.get("ingest_status", ""),
        "ingest_source": proj.get("ingest_source", ""),
        "ingest_error": proj.get("ingest_error", "") or "",
        "state": proj.get("state"),
        "brd_maturity": proj.get("brd_maturity", 0),
    }
