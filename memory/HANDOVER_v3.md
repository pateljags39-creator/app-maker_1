# Local App Creator — Handover v3 (2026-05-13, continuation session)

> Hand-off prompt for the next agent picking up this project mid-flight.
> Pair with `/app/memory/REFERENCE.md` (master), `/app/memory/PRD.md` (changelog),
> `/app/memory/AUDIT.md` (detailed engineering audit). This file summarises **what
> the most recent session added** and **what still needs doing**, so the next agent
> doesn't burn credits re-learning history.

---

## 1. State of the system (as of this writing)

| Concern | Status |
|---|---|
| Backend | ✅ RUNNING (port 8001) |
| Frontend | ✅ RUNNING (port 3000) |
| MongoDB | ✅ RUNNING |
| Gemini primary | ✅ `primary_available=true` (user-supplied key in `backend/.env`) |
| Emergent LLM fallback | ✅ wired |
| Pre-existing tests | ✅ 5 suites pass: `recovery`, `HIGH-1`, `MEDIUM-1`, `HIGH-2`, `HIGH-3/4/5/6` |

**Default LLM models in use** (in `engines/llm_gateway.py`):
- light tier: `gemini-2.5-flash`
- heavy tier: `gemini-2.5-pro`

**User indicated newer models are available on their key** (screenshot 2026-05-13):
Gemini 3 Flash, Gemini 3.1 Flash Lite, Gemini 3.1 Pro, Gemini 3.1 Flash TTS,
Gemini Robotics ER 1.6, Computer Use Preview, Deep Research Pro Preview.
**Recommended upgrade when proceeding**: light → `gemini-3-flash`, heavy → `gemini-3.1-pro`.
This needs only a 2-line change in `engines/llm_gateway.py` (`TIER_MODELS` dict).
Validate primary_available stays `true` after the swap.

---

## 2. What this session shipped (do NOT redo)

### 2a. Platform-level functionality fixes (root-causes of "calculator made a mess")

All six are deterministic post-LLM fixups in `engines/generation_engine.py` and
`engines/build_engine.py`. They run on EVERY future generation automatically.

| ID | File | What it does | Test file |
|---|---|---|---|
| **HIGH-2** | `engines/build_engine.py` `build_frontend()` | Detects stale `package-lock.json` (mtime vs package.json + declared-dep coverage); deletes stale lock and uses `npm install` instead of `npm ci`. Killed the `Rollup failed to resolve import "uuid"` class. | `tests/test_high2_stale_lockfile_fallback.py` (4 tests) |
| **HIGH-3** | `engines/generation_engine.py` `_stub_missing_named_exports_js()` | Replaced silent `(...args) => null` stubs with: (a) smart alias to closest export, ranked by name-similarity + verb category (`get/fetch/list` are read-verbs, `save/create` are write-verbs), (b) loud-throwing stub when no plausible match. Honesty rule preserved. | `tests/test_high345_generation_fixups.py` |
| **HIGH-4** | `engines/generation_engine.py` `_ensure_pydantic_camel_aliases()` | NEW fixup. For every BaseModel-derived class in `backend/**.py` that has snake_case fields AND no own `model_config`, injects `model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)`. Handles transitive inheritance. Bridges JS camelCase ↔ Python snake_case. Killed the "every API call returns 422" class. | same file |
| **HIGH-5** | `engines/generation_engine.py` `_ensure_frontend_uses_relative_api()` | NEW fixup. Rewrites hardcoded `http://localhost:8000` / `127.0.0.1:8000` API base URLs in `frontend/src/**.{js,jsx,ts,tsx}` to empty string (same-origin). Injects a minimal `server.proxy` block into `vite.config.js` if missing. | same file |
| **HIGH-6** | `engines/generation_engine.py` `_fix_python_class_attr_case_mismatches()` | NEW fixup. AST-parses every `backend/**.py`, builds `class_name -> {declared_attrs}` map, scans `ClassName.attr` usages and rewrites camelCase↔snake_case typos (e.g. `DB_Calculation.sessionId` → `.session_id`). Handles import aliases (`from models import Calculation as DB_Calculation`). Killed the "first DB query returns 500 AttributeError" class. | same file |
| env | `backend/requirements.txt` | Bumped `typing_extensions>=4.14.0`. Calculator's pinned `==4.12.0` had downgraded it system-wide and broke `google-genai` SDK → `primary_available=false`. | n/a |

All HIGH-3/4/5/6 tests live in **`tests/test_high345_generation_fixups.py`** (10 tests, 100% pass).

### 2b. NEW: Live Sandbox / Demo feature

User wanted to demo generated apps before exporting. Killer feature — turns the platform from "factory" into "IDE".

**Backend** (new):
- `engines/sandbox_engine.py` — `SandboxRegistry` (thread-safe, atexit cleanup). Methods: `start(project_id, workspace)`, `stop()`, `get()`, `public()`, `touch()`, `log_tail()`, `stop_all()`. Concurrency cap: **MAX_SANDBOXES=3** (LRU-evict on overflow). Idle timeout: **IDLE_LIMIT_S=15min**. Port range: 18000-18100. Spawns `python -m uvicorn main:app --port <dyn>` in `workspace/{id}/backend`. Verifies port opens in ≤10s; otherwise tears down and surfaces error.
- `engines/sandbox_engine.rewrite_api_base_for_sandbox()` — text rewriter. For HTML it injects `<base href="/api/sandbox/{id}/">` and rewrites absolute `src/href="/assets/..."` → relative. For all text it rewrites `"/api/` → `"/api/sandbox/{id}/api/` so generated frontends work inside the proxy URL.
- `routes/sandbox.py` — 5 routes:
  - `POST /api/projects/{id}/sandbox/start`
  - `POST /api/projects/{id}/sandbox/stop`
  - `GET  /api/projects/{id}/sandbox/status`
  - `GET  /api/projects/{id}/sandbox/logs?lines=N`
  - `ANY  /api/sandbox/{id}/{path:path}` — catch-all: API calls (`path` starts with `api/`) proxied via `httpx.AsyncClient`; everything else served from `frontend/dist/`.

**Frontend** (new):
- `pages/Sandbox.jsx` — iframe host + start/stop/reload, log tail viewer (collapsible), idle countdown banner, error surface with sandbox logs auto-popped on failure. data-testid'd: `sandbox-page`, `sandbox-start-btn`, `sandbox-stop-btn`, `sandbox-reload-btn`, `sandbox-iframe`, `sandbox-logs`, `sandbox-error`.
- Wired into `App.js` routes (`/projects/:id/sandbox`).
- Added to `components/cockpit/AppShell.jsx` sidebar (`Sparkles` icon).
- Added to `pages/Cockpit.jsx` landing card grid as a prominent "Sandbox · Run Demo" entry.
- Helpers added to `lib/api.js`: `sandboxStart`, `sandboxStop`, `sandboxStatus`, `sandboxLogs`, `sandboxIframeSrc(id)`.

**Verification:** auto frontend testing agent ran 10-step end-to-end pass. All 10 passed. 22 sandbox API calls, 0 failures.

### 2c. Files created in this session

- `/app/backend/engines/sandbox_engine.py`
- `/app/backend/routes/sandbox.py`
- `/app/backend/tests/test_high2_stale_lockfile_fallback.py`
- `/app/backend/tests/test_high345_generation_fixups.py`
- `/app/frontend/src/pages/Sandbox.jsx`
- `/app/memory/HANDOVER_v3.md` (this file)

### 2d. Files modified

- `/app/backend/engines/build_engine.py` — HIGH-2 stale-lock detection
- `/app/backend/engines/generation_engine.py` — 5 new fixups + improvements to existing `_stub_missing_named_exports_js`
- `/app/backend/routes/__init__.py` — registered `sandbox_router`
- `/app/backend/requirements.txt` — `typing_extensions` bumped
- `/app/backend/.env` — populated with `GEMINI_API_KEY` (user-supplied) and `EMERGENT_LLM_KEY`
- `/app/frontend/.env` — populated with `REACT_APP_BACKEND_URL`
- `/app/frontend/src/App.js` — route for `<SandboxPage>`
- `/app/frontend/src/components/cockpit/AppShell.jsx` — sidebar nav entry
- `/app/frontend/src/pages/Cockpit.jsx` — landing card entry
- `/app/frontend/src/lib/api.js` — sandbox helpers
- `/app/memory/PRD.md` — changelog entries for the above

---

## 3. ACTIVE bugs/limitations the user reported during this session

| # | Symptom | Status | Notes |
|---|---|---|---|
| **B1** | "Add Sandbox button on the homepage or somewhere" — user couldn't find it easily | **Open at handover write** (will be fixed immediately after this doc) | Today's plan: surface a "Run Demo" CTA on the Dashboard project cards + a top-level "Recent Sandboxes" strip. |
| **B2** | "Export — the download zip was not working" | **Open at handover write** (will be reproduced + fixed immediately after this doc) | Check `routes/projects.py` export endpoint, the frontend `Export.jsx` download flow, and the backend's `engines/export_engine.py` ZIP build. Suspect: streaming response, MIME, or filename header. |
| **B3** | "Make the UI good" (planned next phase) | **Pending** — depends on credits | User chose **Gemini 3.1 Pro** route. To be done with `gemini-3.1-pro` model swap; redesign of Dashboard, Cockpit, Build, Sandbox pages with stronger visual identity (gradients, glassmorphism, motion). Pacing: incremental — don't redo backend logic, only frontend visual layer. |

---

## 4. Strategic backlog (from upstream handoff, still open)

Carried forward from the previous handoff document. **Order = recommended priority** for next sessions after B1/B2/B3 are done.

### High-impact, 1-3 sessions each
1. **Phase 4 Ingest UI polish (P2)** — backend Ingest works (ZIP + git URL → BRD-from-code), but `Ingest.jsx` is bare. Add drag-drop, paste-URL, progress, "Modernize this project" CTA.
2. **Configurable repair retry budget (MEDIUM-2, P2)** — currently hard-coded to 2. Surface as a number field on `Constraints.jsx`.
3. **Phase 5 component-library lookup (P2)** — curate safe React+FastAPI fragments (auth shell, CRUD form, pagination, file-upload) the planner can reference.
4. **Preview diff before apply on Improve (P3)** — cache the manifest, render diff, gate apply behind explicit accept. Eliminates wasted rebuilds.
5. **Polish (P3)** — react-hooks warnings, requirements.txt trim, fix `build.overall_status=null` for empty plans.

### Strategic (2-3+ sessions each)
- **Multi-stack contracts** — pluggable generation contract (Next.js, Hono, Postgres/Supabase) so it's not just React+FastAPI.
- **Generation cache + dedupe** — content-addressed hash of `{brd+arch+plan.file}`. 40–60% spend reduction on common app types.
- **Repair budget self-tuning** — analytics-driven.
- **Project share/collaborate** — link-based read-only project view.
- **Generation quality dashboard** — per-project acceptance/repair metrics over time.
- **Phase 6 Continuous Improve** — long-running goal-mode where the agent iterates against a quality target.
- **Onboarding wizard** — 90-second guided demo that produces a working todo app on first run.

---

## 5. Critical "gotchas" / things to NOT touch

1. **DO NOT modify env vars in `backend/.env` or `frontend/.env`** other than user-supplied keys. `MONGO_URL`, `REACT_APP_BACKEND_URL` are correct as-is. The Kubernetes ingress routes `/api/*` → backend:8001 and `/*` → frontend:3000.
2. **DO NOT swap `npm ci` back to default-on.** HIGH-2 fix depends on the freshness check.
3. **DO NOT remove the `<base href>` injection in `rewrite_api_base_for_sandbox`** — without it, generated frontends' `<script src="/assets/...">` resolves to the cockpit, not the sandbox, and you'll get a blank page.
4. **DO NOT install workspace requirements.txt into the cockpit venv.** It will downgrade typing_extensions and break google-genai. If you must, do it in a temp venv (`python -m venv /tmp/calcvenv && /tmp/calcvenv/bin/pip install -r ...`).
5. **DO NOT call `_stub_missing_named_exports_js` after manually mucking with a workspace's api.js.** It is idempotent on its own marker line, but the marker is `// AUTO-STUB:` — preserve that.
6. **Sandbox processes are NOT in supervisor.** They live in `SandboxRegistry` in-memory + as detached process groups. When the cockpit backend restarts, they die with it (atexit). This is the intended design.

---

## 6. How to verify everything is alive (90-second checkup)

```bash
# 1. Services
sudo supervisorctl status

# 2. Backend health (expect primary_available=true)
curl -s http://localhost:8001/api/system/health | python -m json.tool

# 3. All unit tests
cd /app/backend
for t in test_recovery_engine test_high1_frontend_only_gating \
         test_medium1_endpoint_verification test_high2_stale_lockfile_fallback \
         test_high345_generation_fixups; do
  echo "=== $t ==="
  python tests/$t.py 2>&1 | tail -1
done

# 4. Sandbox routes registered (expect 5 paths with /sandbox)
curl -s http://localhost:8001/openapi.json \
  | python -c "import sys,json; d=json.load(sys.stdin); print('\n'.join(p for p in d['paths'] if 'sandbox' in p))"
```

Expected outputs:
- All services `RUNNING`
- `primary_available=true`, `fallback_available=true`
- Every test prints `All ... tests passed.`
- 5 sandbox paths present

---

## 7. If credits wipe in the middle of B1/B2/B3 work

Resume order:
1. **B1 (homepage Sandbox button)** is a 10-minute frontend-only change. Likely already done by the time this matters. Look at `pages/Dashboard.jsx` for a "Run Demo" card per project.
2. **B2 (export ZIP broken)** needs investigation. Start with:
   ```bash
   grep -n "export\|zip\|StreamingResponse" /app/backend/routes/projects.py /app/backend/engines/export_engine.py
   ```
   Then test directly: `curl -s -o /tmp/x.zip "http://localhost:8001/api/projects/{id}/export" -v` and check headers / body. The frontend `Export.jsx` likely uses `<a download>` against a URL — verify the response sets `Content-Disposition: attachment`.
3. **B3 (UI redesign)** — pure frontend. Swap models in `engines/llm_gateway.py` `TIER_MODELS` to `gemini-3.1-pro` / `gemini-3-flash` first; then redesign one page at a time. Keep the data-testid attributes intact for the testing agent.

---

## 8. The user's working style (so you don't waste their time)

- They want **functionality before polish**. UI is a stretch goal.
- They are **credit-conscious**. Ask before burning Pro calls.
- They prefer **option a/b/c** style questions, not open-ended.
- They like **concrete next steps** in every reply.
- They will **say "c" to skip validation** if they trust you — don't over-validate when they push to move on.

---

— End of Handover v3 —
