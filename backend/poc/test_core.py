"""POC core test for Local App Creator.

This single script proves the entire core hypothesis:
  1) LLM gateway: direct Gemini primary -> Emergent universal-key fallback.
  2) BRD engine: questions + maturity derive from a free-form idea.
  3) Architecture engine: classifies a notes app as full_stack.
  4) Generation engine: produces a React+Vite + FastAPI + SQLite scaffold.
  5) Build engine: runs npm install + npm run build, pip install + import check.
  6) Repair engine: on failure, asks LLM for a safe single-file patch, retries.
  7) Acceptance engine: honest PASS/PARTIAL/FAIL checks.
  8) Export engine: produces a clean ZIP with manifest and scrubs secrets.

Run from /app/backend with:
    cd /app/backend && python poc/test_core.py

Exit code: 0 on PASS, 2 on PARTIAL (acceptable for first iteration), 1 on FAIL.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

# Make `engines` importable when run as: python poc/test_core.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

from engines.acceptance_engine import run_acceptance  # noqa: E402
from engines.architecture_engine import detect_architecture  # noqa: E402
from engines.brd_engine import derive_brd, generate_questions  # noqa: E402
from engines.build_engine import run_build  # noqa: E402
from engines.export_engine import export_project  # noqa: E402
from engines.generation_engine import generate_project  # noqa: E402
from engines.llm_gateway import LLMGateway  # noqa: E402
from engines.repair_engine import attempt_repairs  # noqa: E402
from engines.snapshot_engine import create_snapshot  # noqa: E402


WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_DIR", "/app/workspace")) / "projects"
WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)


def hr(title: str) -> None:
    print(f"\n{'='*72}\n{title}\n{'='*72}")


async def main() -> int:
    overall_started = time.monotonic()
    project_id = f"poc-{int(time.time())}"
    workspace = WORKSPACE_ROOT / project_id

    hr(f"POC project_id={project_id}  workspace={workspace}")

    gateway = LLMGateway()
    print("LLM status:", json.dumps(gateway.status(), indent=2))

    # ---------- Step 1: BRD engine smoke ----------
    hr("Step 1: BRD engine -- questions + derive BRD from free-form idea")
    idea = (
        "I want a simple personal notes app. I should be able to create notes "
        "(with title and body), list all my notes, view a note, and delete a note. "
        "It should work offline-friendly on my laptop. No login needed."
    )
    questions = await generate_questions(gateway, idea)
    print(f"  generated {len(questions)} SME questions:")
    for q in questions[:3]:
        print(f"   - [{q.get('category')}] {q.get('text')}")
    # Simulate user answers for POC.
    qa_pairs = [
        {"question_id": q.get("id", f"q{i+1}"), "question": q.get("text", ""),
         "answer": "Single user, local-first, notes have id/title/body/created_at; delete and edit allowed; list newest first."}
        for i, q in enumerate(questions[:5])
    ]
    brd = await derive_brd(gateway, idea, qa_pairs)
    print("  BRD maturity:", brd.get("maturity", {}).get("score"))
    print("  BRD requirements:", len(brd.get("requirements", [])))

    # ---------- Step 2: Architecture detection ----------
    hr("Step 2: Architecture detection -- expect full_stack")
    arch = detect_architecture(brd).to_dict()
    print(f"  architecture.kind = {arch['kind']}")
    print(f"  requires_backend  = {arch['requires_backend']}")
    print(f"  requires_database = {arch['requires_database']}")
    assert arch["kind"] in ("full_stack", "backend_required"), f"Unexpected: {arch['kind']}"

    # ---------- Step 3: Generation ----------
    hr("Step 3: Generation engine -- write React+Vite + FastAPI + SQLite scaffold")
    gen = await generate_project(gateway, brd, arch, workspace)
    print(f"  wrote {len(gen.files_written)} files into {gen.workspace}")
    for f in gen.files_written[:15]:
        print(f"   - {f}")

    # Snapshot before build
    snap = create_snapshot(workspace, label="post_generation")
    print(f"  snapshot {snap.id} sha256={snap.sha256[:12]} files={snap.files}")

    # ---------- Step 4: Build + Repair loop ----------
    hr("Step 4: Build + Repair (max 2 retries)")
    build = await run_build(workspace, project_id)
    print(f"  initial build overall = {build.overall_status}; "
          f"fe_pass={build.summary['frontend_pass']} be_pass={build.summary['backend_pass']}")
    if build.overall_status != "PASS":
        build, repair = await attempt_repairs(workspace, project_id, gateway, max_retries=2, initial_build=build)
        print(f"  after repair: status={build.overall_status}; attempts={len(repair.attempts)}")
        for a in repair.attempts:
            print(f"   - attempt {a.attempt}: cls={a.classification} step={a.target_step} "
                  f"applied={a.patch_applied} after={a.build_after} note={a.note[:90]!r}")

    # ---------- Step 5: Acceptance ----------
    hr("Step 5: Acceptance checks")
    acc = run_acceptance(workspace, brd, arch, build_summary=build.to_dict())
    print(f"  overall acceptance = {acc.overall}; checks={len(acc.checks)}")
    for c in acc.checks:
        print(f"   [{c.status:7}] {c.name}: {c.detail[:80]}")

    # ---------- Step 6: Export ----------
    hr("Step 6: Export ZIP")
    exp = export_project(workspace, project_name=brd.get("app_name") or project_id)
    print(f"  exported: {exp.path}")
    print(f"  files={exp.files} size_bytes={exp.size_bytes} secrets_detected={exp.secret_findings}")
    print(f"  manifest: {exp.manifest_path}")
    assert exp.secret_findings == 0, "Secret findings in export -- HARD FAIL"

    # ---------- Verdict ----------
    duration = round(time.monotonic() - overall_started, 1)
    hr(f"POC verdict (took {duration}s)")
    final = "FAIL"
    if build.overall_status == "PASS" and acc.overall in ("PASS", "PARTIAL"):
        final = "PASS"
    elif build.overall_status in ("PARTIAL",) and acc.overall in ("PASS", "PARTIAL"):
        final = "PARTIAL"
    print(f"  BUILD={build.overall_status}  ACCEPTANCE={acc.overall}  EXPORT=OK  ==> {final}")

    if final == "PASS":
        return 0
    if final == "PARTIAL":
        return 2
    return 1


if __name__ == "__main__":
    try:
        rc = asyncio.run(main())
    except Exception as e:  # surface honest error
        print(f"\nPOC CRASHED: {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        rc = 1
    sys.exit(rc)
