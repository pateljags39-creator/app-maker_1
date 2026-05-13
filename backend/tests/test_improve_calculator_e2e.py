"""End-to-end smoke test for the Improve/Fix engine using a tiny calculator app.

Designed to use **exactly one** Pro (heavy) LLM call to validate the full
snapshot -> manifest -> validate -> apply -> rebuild -> (rollback?) -> acceptance
pipeline on a real, but minimal, workspace.

Run with:  cd /app/backend && python -m tests.test_improve_calculator_e2e
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import time
from pathlib import Path

# Allow `import backend.*` style as well as direct `engines.*` from /app/backend
HERE = Path(__file__).resolve()
BACKEND_DIR = HERE.parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(BACKEND_DIR / ".env")

import db  # noqa: E402
import repositories as repo  # noqa: E402
from engines.improve_engine import request_improve  # noqa: E402
from engines.llm_gateway import LLMGateway  # noqa: E402


WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_DIR", "/app/workspace"))


CALC_INDEX_HTML = """<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>Tiny Calculator</title>
  </head>
  <body>
    <div id=\"root\"></div>
    <script type=\"module\" src=\"/src/main.jsx\"></script>
  </body>
</html>
"""

CALC_MAIN_JSX = """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
"""

CALC_APP_JSX = """import React, { useState } from 'react';

export default function App() {
  const [display, setDisplay] = useState('0');

  const press = (k) => {
    if (k === 'C') return setDisplay('0');
    if (k === '=') {
      try {
        // eslint-disable-next-line no-eval
        const v = eval(display);
        return setDisplay(String(v));
      } catch (e) {
        return setDisplay('Err');
      }
    }
    setDisplay((d) => (d === '0' ? String(k) : d + String(k)));
  };

  const keys = ['7','8','9','/','4','5','6','*','1','2','3','-','0','.','=','+'];
  return (
    <div style={{fontFamily:'sans-serif',padding:24}}>
      <h1>Tiny Calculator</h1>
      <div data-testid=\"display\" style={{padding:12,border:'1px solid #ccc',marginBottom:12,fontSize:24}}>{display}</div>
      <div style={{display:'grid',gridTemplateColumns:'repeat(4,60px)',gap:8}}>
        {keys.map((k) => (
          <button key={k} data-testid={`key-${k}`} onClick={() => press(k)}>{k}</button>
        ))}
        <button data-testid=\"key-clear\" onClick={() => press('C')}>C</button>
      </div>
    </div>
  );
}
"""

CALC_PACKAGE_JSON = {
    "name": "tiny-calculator",
    "private": True,
    "version": "0.0.1",
    "type": "module",
    "scripts": {
        "dev": "vite",
        "build": "vite build",
    },
    "dependencies": {
        "react": "^18.3.1",
        "react-dom": "^18.3.1",
    },
    "devDependencies": {
        "@vitejs/plugin-react": "^4.3.1",
        "vite": "^5.4.0",
    },
}

CALC_VITE_CONFIG = """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({ plugins: [react()] });
"""

CALC_README = "# Tiny Calculator\n\nA minimal Vite+React calculator used for Improve/Fix smoke tests.\n"


def seed_workspace(ws: Path) -> None:
    if ws.exists():
        shutil.rmtree(ws)
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "frontend").mkdir(parents=True, exist_ok=True)
    (ws / "frontend" / "src").mkdir(parents=True, exist_ok=True)
    (ws / "frontend" / "index.html").write_text(CALC_INDEX_HTML, encoding="utf-8")
    (ws / "frontend" / "src" / "main.jsx").write_text(CALC_MAIN_JSX, encoding="utf-8")
    (ws / "frontend" / "src" / "App.jsx").write_text(CALC_APP_JSX, encoding="utf-8")
    (ws / "frontend" / "package.json").write_text(json.dumps(CALC_PACKAGE_JSON, indent=2) + "\n", encoding="utf-8")
    (ws / "frontend" / "vite.config.js").write_text(CALC_VITE_CONFIG, encoding="utf-8")
    (ws / "README.md").write_text(CALC_README, encoding="utf-8")


CALC_BRD = {
    "description": "A tiny browser-based calculator: digits, four operators, equals, clear.",
    "requirements": [
        {"id": "R1", "text": "Display digits as the user presses number buttons", "status": "supported"},
        {"id": "R2", "text": "Support add, subtract, multiply, divide operators", "status": "supported"},
        {"id": "R3", "text": "Equals button computes and displays the result", "status": "supported"},
        {"id": "R4", "text": "Clear button resets the display to 0", "status": "supported"},
    ],
    "forced_architecture": "frontend_only",
}

CALC_PLAN = {
    "summary": "Vite+React single-page calculator",
    "files": [
        {"path": "frontend/index.html"},
        {"path": "frontend/src/main.jsx"},
        {"path": "frontend/src/App.jsx"},
        {"path": "frontend/package.json"},
        {"path": "frontend/vite.config.js"},
    ],
    "endpoints": [],
    "entities": [],
}

CALC_ARCH = {
    "kind": "frontend_only",
    "reasoning": ["UI only; no persistence/api"],
    "requires_backend": False,
    "requires_database": False,
    "blocked": False,
    "block_reasons": [],
    "limited_prototype_accepted": False,
}


async def main() -> int:
    project_id = "calc-improve-smoke"
    ws = WORKSPACE_ROOT / "projects" / project_id

    # 1) Seed workspace + Mongo records (no LLM calls).
    seed_workspace(ws)
    db.init_client()

    # Clean prior state
    mdb = db.get_db()
    await mdb.projects.delete_one({"id": project_id})
    await mdb.brds.delete_many({"project_id": project_id})
    await mdb.architectures.delete_many({"project_id": project_id})
    await mdb.plans.delete_many({"project_id": project_id})
    await mdb.improve_attempts.delete_many({"project_id": project_id})

    await mdb.projects.insert_one({
        "id": project_id,
        "name": "Tiny Calculator (Improve smoke)",
        "idea": "Tiny browser-only calculator used to smoke-test Improve/Fix.",
        "state": "Acceptance",
        "workspace_dir": str(ws),
        "brd_maturity": 100,
        "last_build_status": "PASS",  # pretend it built clean
        "last_acceptance_status": "PASS",
        "ingested": False,
        "ingest_source": "",
        "ingest_status": "",
        "ingest_error": "",
        "created_at": time.time(),
        "updated_at": time.time(),
    })
    await repo.upsert_brd(project_id, brd=CALC_BRD, maturity=100)
    await repo.upsert_architecture(project_id, CALC_ARCH)
    await repo.upsert_plan(project_id, CALC_PLAN)

    # Set a small constraints budget — calculator changes should easily fit.
    await repo.set_constraints(project_id, {
        "max_files_changed": 4,
        "max_new_files": 2,
        "max_total_loc_changed": 400,
        "allowed_areas": ["frontend/"],
        "no_new_top_level_dirs": True,
        "allow_npm_dep_changes": False,
        "allow_pip_dep_changes": False,
        "notes": "Calculator Improve/Fix smoke test budget",
    })
    constraints = await repo.get_constraints(project_id)

    # 2) Run a *real* Improve call (exactly 1 Pro call).
    print("--- Running request_improve with 1 Pro LLM call ---", flush=True)
    gw = LLMGateway()
    attempt = await request_improve(
        gateway=gw,
        workspace=ws,
        project_id=project_id,
        brd=CALC_BRD,
        plan=CALC_PLAN,
        arch=CALC_ARCH,
        change_request="Add a 'sqrt' (square-root) button next to the 'C' button. When clicked, replace the display with the square root of the current display value. Update App.jsx only.",
        constraints=constraints,
        last_build_status="PASS",
    )

    out = attempt.to_dict()
    print("status:", out["status"], flush=True)
    print("summary:", out["summary"], flush=True)
    print("violations:", out["violations"], flush=True)
    print("files_changed:", [f["path"] for f in out["files_changed"]], flush=True)
    print("build_before:", out["build_before"], "build_after:", out["build_after"], flush=True)
    print("acceptance_after:", out["acceptance_after"], flush=True)
    print("rolled_back:", out["rolled_back"], flush=True)
    print("error:", out["error"], flush=True)

    rec = await repo.add_improve_attempt(project_id, out)
    print("persisted attempt id:", rec.get("id"), flush=True)

    # Print the final App.jsx if applied so we can eyeball the LLM output.
    app_jsx = ws / "frontend" / "src" / "App.jsx"
    if app_jsx.exists():
        text = app_jsx.read_text("utf-8")
        print("--- App.jsx (head) ---", flush=True)
        print(text[:2000], flush=True)

    return 0 if out["status"] in {"applied", "rolled_back"} else 1


if __name__ == "__main__":
    rc = asyncio.run(main())
    sys.exit(rc)
