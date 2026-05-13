"""Routes: full generation pipeline (background task)."""
from __future__ import annotations

import asyncio
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, HTTPException

from engines.acceptance_engine import run_acceptance
from engines.export_engine import export_project
from engines.generation_engine import generate_project
from engines.llm_gateway import LLMGateway
from engines.repair_engine import attempt_repairs
from engines.snapshot_engine import create_snapshot
from event_ledger import get_ledger
import repositories as repo

router = APIRouter(prefix="/projects/{project_id}", tags=["generate"])

_active_jobs: dict[str, asyncio.Task] = {}


async def _run_pipeline(project_id: str, auto_prepare: bool = False) -> None:
    led = get_ledger()
    proj = await repo.get_project(project_id)
    if not proj:
        return
    workspace = Path(proj["workspace_dir"])
    workspace.mkdir(parents=True, exist_ok=True)

    # If auto_prepare is True, ensure architecture + plan exist before generation.
    if auto_prepare:
        try:
            from engines.architecture_engine import detect_architecture
            from engines.generation_engine import generate_plan as _gen_plan
            from engines.llm_gateway import LLMGateway as _GW
            brd_doc = await repo.get_brd(project_id)
            brd = (brd_doc or {}).get("brd") or {}
            if not brd or not brd.get("requirements"):
                await led.emit_simple(project_id, "pipeline.error",
                                      "Cannot run pipeline: BRD has no requirements yet. Answer some BRD questions first.",
                                      severity="error")
                return
            arch_doc = await repo.get_architecture(project_id)
            decision = (arch_doc or {}).get("decision") or {}
            if not decision.get("kind"):
                await led.emit_simple(project_id, "architecture.auto_detect",
                                      "Auto-detecting architecture from BRD",
                                      severity="info")
                decision = detect_architecture(brd).to_dict()
                await repo.upsert_architecture(project_id, decision)
                await repo.set_state(project_id, "Architecture")
                await led.emit_simple(project_id, "architecture.detected",
                                      f"Architecture: {decision['kind']}",
                                      payload={"kind": decision["kind"], "blocked": decision["blocked"]},
                                      severity="warning" if decision["blocked"] else "success")
            if decision.get("blocked"):
                await led.emit_simple(project_id, "pipeline.error",
                                      f"Architecture blocked: {decision.get('block_reasons')}. "
                                      "Visit the Architecture page to override.",
                                      severity="error")
                return
            plan_doc = await repo.get_plan(project_id)
            if not plan_doc or not (plan_doc.get("plan") or {}).get("files"):
                await led.emit_simple(project_id, "plan.auto_generate",
                                      "Auto-generating file plan",
                                      severity="info")
                gw = _GW()
                plan = await _gen_plan(gw, brd, decision)
                await repo.upsert_plan(project_id, plan)
                await repo.set_state(project_id, "Plan")
                await led.emit_simple(project_id, "plan.generated",
                                      f"Plan with {len(plan.get('files', []))} files",
                                      payload={"files": len(plan.get("files", []))},
                                      severity="success")
        except Exception as e:
            await led.emit_simple(project_id, "pipeline.error",
                                  f"Auto-prepare failed: {type(e).__name__}: {str(e)[:200]}",
                                  severity="error")
            return
        # Refresh project doc post-prep
        proj = await repo.get_project(project_id)
        if not proj:
            return

    brd_doc = await repo.get_brd(project_id)
    arch_doc = await repo.get_architecture(project_id)
    brd = (brd_doc or {}).get("brd") or {}
    arch = (arch_doc or {}).get("decision") or {}
    if not brd or not arch:
        await led.emit_simple(project_id, "pipeline.error", "Missing BRD or architecture", severity="error")
        return
    try:
        gw = LLMGateway()
        await led.emit_simple(project_id, "generation.started",
                              f"Generating scaffold using {gw.model}", severity="info")
        await repo.set_state(project_id, "Generating")

        gen = await generate_project(gw, brd, arch, workspace)
        await led.emit_simple(project_id, "generation.completed",
                              f"Wrote {len(gen.files_written)} files",
                              payload={"files": gen.files_written[:30]}, severity="success")
        try:
            snap = create_snapshot(workspace, label="post_generation")
            await led.emit_simple(project_id, "snapshot.created",
                                  f"Snapshot {snap.id}", payload={"id": snap.id, "files": snap.files},
                                  severity="info")
        except Exception as e:
            await led.emit_simple(project_id, "snapshot.error", f"Snapshot failed: {e}", severity="warning")

        await repo.set_state(project_id, "Building")
        await led.emit_simple(project_id, "build.started", "Running build (npm + pip + import)", severity="info")

        from engines.build_engine import run_build
        build = await run_build(workspace, project_id)
        await led.emit_simple(project_id, "build.completed",
                              f"Build {build.overall_status}",
                              payload={"status": build.overall_status, "summary": build.summary},
                              severity="success" if build.overall_status == "PASS" else (
                                  "warning" if build.overall_status == "PARTIAL" else "error"))

        repair_dict: dict = {}
        if build.overall_status != "PASS":
            await repo.set_state(project_id, "Repair")
            await led.emit_simple(project_id, "repair.started", "Attempting safe repairs", severity="warning")
            constraints = await repo.get_constraints(project_id)
            build, outcome = await attempt_repairs(
                workspace, project_id, gw, max_retries=2,
                initial_build=build, constraints=constraints,
            )
            repair_dict = outcome.to_dict()
            for attempt in outcome.attempts:
                await led.emit_simple(project_id, "repair.attempt",
                                      f"Attempt {attempt.attempt}: {attempt.classification} -> {attempt.build_after}",
                                      payload={
                                          "attempt": attempt.attempt,
                                          "file": attempt.target_file,
                                          "step": attempt.target_step,
                                          "applied": attempt.patch_applied,
                                          "note": attempt.note[:200],
                                      },
                                      severity="info" if attempt.patch_applied else "warning")
            await led.emit_simple(project_id, "repair.completed",
                                  f"Final after repair: {build.overall_status}",
                                  payload={"status": build.overall_status,
                                          "attempts": len(outcome.attempts)},
                                  severity="success" if build.overall_status == "PASS" else "warning")

        await repo.add_build(project_id, build.to_dict(), repair_dict)
        await repo.update_project(project_id, last_build_status=build.overall_status)

        await repo.set_state(project_id, "Acceptance")
        await led.emit_simple(project_id, "acceptance.started", "Running acceptance checks", severity="info")
        report = run_acceptance(workspace, brd, arch, build_summary=build.to_dict())
        await repo.add_acceptance(project_id, report.to_dict())
        await repo.update_project(project_id, last_acceptance_status=report.overall)
        await led.emit_simple(project_id, "acceptance.completed",
                              f"Acceptance {report.overall}",
                              payload={"overall": report.overall, "checks": len(report.checks)},
                              severity="success" if report.overall == "PASS" else (
                                  "warning" if report.overall == "PARTIAL" else "error"))

        # Auto-export on PASS / PARTIAL
        if report.overall in ("PASS", "PARTIAL"):
            await repo.set_state(project_id, "Export")
            exp = export_project(workspace, project_name=(proj.get("name") or project_id).strip() or project_id)
            await repo.add_export(project_id, {
                "path": exp.path, "sha256": exp.sha256, "files": exp.files,
                "size_bytes": exp.size_bytes, "secret_findings": exp.secret_findings,
                "manifest_path": exp.manifest_path, "created_at": exp.created_at,
            })
            await repo.update_project(project_id, last_export_path=exp.path)
            await led.emit_simple(project_id, "export.completed",
                                  f"Exported {Path(exp.path).name}",
                                  payload={"files": exp.files, "size_bytes": exp.size_bytes,
                                          "secrets": exp.secret_findings},
                                  severity="success")
        else:
            await led.emit_simple(project_id, "export.skipped",
                                  f"Skipped export: acceptance={report.overall}",
                                  severity="warning")
    except Exception as e:
        await led.emit_simple(project_id, "pipeline.error",
                              f"{type(e).__name__}: {str(e)[:200]}", severity="error")
    finally:
        _active_jobs.pop(project_id, None)


@router.post("/generate")
async def trigger_generate(project_id: str, background: BackgroundTasks):
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(404, "project_not_found")
    if project_id in _active_jobs and not _active_jobs[project_id].done():
        raise HTTPException(409, "pipeline_already_running")
    arch_doc = await repo.get_architecture(project_id)
    if not arch_doc or not (arch_doc.get("decision") or {}).get("kind"):
        raise HTTPException(400, "architecture_not_detected")
    if arch_doc["decision"].get("blocked"):
        raise HTTPException(409, "architecture_blocked")
    task = asyncio.create_task(_run_pipeline(project_id))
    _active_jobs[project_id] = task
    return {"status": "started", "project_id": project_id}


@router.post("/run_full_pipeline")
async def run_full_pipeline(project_id: str):
    """One-click: auto-detect architecture, auto-generate plan, then run the full pipeline.

    Used by the dashboard / BRD page once BRD has enough maturity.
    """
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(404, "project_not_found")
    if project_id in _active_jobs and not _active_jobs[project_id].done():
        raise HTTPException(409, "pipeline_already_running")
    brd_doc = await repo.get_brd(project_id)
    brd = (brd_doc or {}).get("brd") or {}
    if not brd or not brd.get("requirements"):
        raise HTTPException(400, "brd_not_ready: answer some BRD questions first")
    task = asyncio.create_task(_run_pipeline(project_id, auto_prepare=True))
    _active_jobs[project_id] = task
    return {"status": "started", "project_id": project_id, "mode": "auto_prepare"}


@router.get("/generate/status")
async def status(project_id: str):
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(404, "project_not_found")
    running = project_id in _active_jobs and not _active_jobs[project_id].done()
    return {"running": running, "state": proj["state"],
            "last_build_status": proj.get("last_build_status"),
            "last_acceptance_status": proj.get("last_acceptance_status")}
