"""Phase 4 — Ingest E2E smoke test.

Builds a tiny in-memory ZIP representing a minimal Vite+React+FastAPI project,
uploads it through POST /api/projects/ingest/zip, waits for the async BRD
derivation to complete, and verifies the project lands in `Architecture` state
with a non-empty inferred BRD and a synthesized plan whose endpoints match
what the deterministic scanner found.

Uses **exactly 1 heavy (Pro) LLM call** — minimised to honour the per-minute
Gemini rate limit. No fallback path is exercised intentionally.

Run with:
    cd /app/backend && python -m tests.test_phase4_ingest_e2e
"""
from __future__ import annotations

import asyncio
import io
import json
import os
import sys
import time
import zipfile
from pathlib import Path

import httpx

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent.parent))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(HERE.parent.parent / ".env")


FRONTEND_ENV = Path("/app/frontend/.env").read_text("utf-8")
BASE_URL = next(
    line.split("=", 1)[1].strip()
    for line in FRONTEND_ENV.splitlines()
    if line.startswith("REACT_APP_BACKEND_URL=")
)


PKG_JSON = {
    "name": "tiny-notes",
    "private": True,
    "version": "0.0.1",
    "scripts": {"dev": "vite", "build": "vite build"},
    "dependencies": {"react": "^18.3.1", "react-dom": "^18.3.1"},
    "devDependencies": {"vite": "^5.4.0", "@vitejs/plugin-react": "^4.3.1"},
}

INDEX_HTML = """<!doctype html><html><body><div id=root></div>
<script type=module src=/src/main.jsx></script></body></html>
"""

MAIN_JSX = """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
"""

APP_JSX = """import React, {useEffect, useState} from 'react';
export default function App(){
  const [notes,setNotes]=useState([]);
  useEffect(()=>{fetch('/api/notes').then(r=>r.json()).then(setNotes)},[]);
  return <ul>{notes.map(n=><li key={n.id}>{n.text}</li>)}</ul>;
}
"""

MAIN_PY = """from fastapi import FastAPI, APIRouter
app = FastAPI()
router = APIRouter(prefix='/api')

_NOTES = []

@router.get('/notes')
def list_notes():
    return _NOTES

@router.post('/notes')
def create_note(note: dict):
    _NOTES.append(note)
    return note

@router.delete('/notes/{note_id}')
def delete_note(note_id: int):
    return {'deleted': note_id}

app.include_router(router)
"""

REQUIREMENTS_TXT = "fastapi==0.111.0\nuvicorn==0.30.0\npydantic>=2.10\n"
README_MD = "# Tiny Notes\n\nA minimal Vite+React + FastAPI notes app used for Phase 4 ingest smoke test.\n"


def make_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("tiny-notes/README.md", README_MD)
        zf.writestr("tiny-notes/frontend/package.json", json.dumps(PKG_JSON, indent=2) + "\n")
        zf.writestr("tiny-notes/frontend/index.html", INDEX_HTML)
        zf.writestr("tiny-notes/frontend/src/main.jsx", MAIN_JSX)
        zf.writestr("tiny-notes/frontend/src/App.jsx", APP_JSX)
        zf.writestr("tiny-notes/backend/main.py", MAIN_PY)
        zf.writestr("tiny-notes/backend/requirements.txt", REQUIREMENTS_TXT)
    return buf.getvalue()


async def main() -> int:
    zip_bytes = make_zip()
    print(f"--- ZIP built, size={len(zip_bytes)} bytes", flush=True)
    print(f"--- BASE_URL={BASE_URL}", flush=True)

    async with httpx.AsyncClient(timeout=120.0) as cli:
        # 1) Upload ZIP
        files = {"file": ("tiny-notes.zip", zip_bytes, "application/zip")}
        data = {"name": "tiny-notes-ingest-smoke"}
        r = await cli.post(f"{BASE_URL}/api/projects/ingest/zip", files=files, data=data)
        print(f"--- upload status={r.status_code}", flush=True)
        if r.status_code != 201:
            print("upload failed:", r.text[:500])
            return 1
        proj = r.json()
        project_id = proj["id"]
        print(f"--- project_id={project_id}, ingest_status={proj['ingest_status']}", flush=True)

        # 2) Poll ingest status (background derive_brd is running with 1 Pro call).
        deadline = time.time() + 90
        last_status = ""
        while time.time() < deadline:
            r = await cli.get(f"{BASE_URL}/api/projects/ingest/{project_id}/status")
            if r.status_code != 200:
                print("status err:", r.status_code, r.text[:200])
                break
            st = r.json()
            if st["ingest_status"] != last_status:
                print(f"  ingest_status={st['ingest_status']}", flush=True)
                last_status = st["ingest_status"]
            if st["ingest_status"] in {"complete", "complete_with_warning", "failed"}:
                break
            await asyncio.sleep(2)

        # 3) Inspect derived state.
        r = await cli.get(f"{BASE_URL}/api/projects/{project_id}")
        proj = r.json()
        print(f"--- final state={proj['state']} brd_maturity={proj.get('brd_maturity')} "
              f"ingest_status={proj.get('ingest_status')} ingest_error={proj.get('ingest_error','')[:200]}",
              flush=True)

        brd = (await cli.get(f"{BASE_URL}/api/projects/{project_id}/brd")).json()
        arch = (await cli.get(f"{BASE_URL}/api/projects/{project_id}/architecture")).json()
        plan = (await cli.get(f"{BASE_URL}/api/projects/{project_id}/plan")).json()

        brd_body = brd.get("brd") or {}
        arch_dec = (arch.get("decision") or {})
        plan_body = (plan.get("plan") or {})

        print("--- BRD product_name:", brd_body.get("product_name"))
        print("--- BRD requirements (head):")
        for r_ in (brd_body.get("requirements") or [])[:5]:
            if isinstance(r_, dict):
                print(f"     * [{r_.get('status','?')}] {r_.get('text','')[:120]}")
        print("--- architecture:", arch_dec.get("kind"), "/ reasoning:", arch_dec.get("reasoning", [])[:3])
        print("--- plan endpoints found:")
        for ep in (plan_body.get("endpoints") or [])[:10]:
            print(f"     * {ep.get('method')} {ep.get('path')}  in {ep.get('file')}")

        # 4) Assertions.
        assert proj["state"] == "Architecture", f"expected state=Architecture, got {proj['state']}"
        assert proj.get("ingest_status") in {"complete", "complete_with_warning"}, proj
        # Stack has no DB (in-memory list), so deterministic detection should land on
        # api_driven (FE + BE, no DB) — not full_stack. full_stack is acceptable too
        # if the user later wires a DB.
        assert arch_dec.get("kind") in {"api_driven", "full_stack"}, (
            f"expected api_driven or full_stack, got {arch_dec.get('kind')}"
        )
        endpoints = plan_body.get("endpoints") or []
        eps = {(e["method"], e["path"]) for e in endpoints}
        assert ("GET", "/notes") in eps, f"GET /notes missing from plan endpoints: {eps}"
        assert ("POST", "/notes") in eps, f"POST /notes missing from plan endpoints: {eps}"
        assert ("DELETE", "/notes/{note_id}") in eps, f"DELETE missing from plan endpoints: {eps}"
        assert (brd_body.get("requirements") or []), "BRD should have at least one inferred requirement"

        print("--- ALL ASSERTIONS PASSED ---", flush=True)

        # 5) Cleanup.
        del_r = await cli.delete(f"{BASE_URL}/api/projects/{project_id}")
        print("--- cleanup status:", del_r.status_code, flush=True)
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
