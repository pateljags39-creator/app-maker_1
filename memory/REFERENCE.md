# Local App Creator — Master Reference
> **Read this FIRST when continuing development.** It tells any AI agent (or human) exactly where everything lives and what's already done.

Last updated: 2026-02-13

---

## What is this app?
Local App Creator is a local-first AI software-factory cockpit. It takes a BRD, generates a real React+Vite + FastAPI + SQLite app, runs real npm/pip builds, repairs failures within a bounded patch budget, supports Improve/Fix and ingest-existing-repo workflows, and exports clean ZIPs with manifests.

**Non-negotiables**: no fake APIs, no silent fallbacks, explicit `unsupported`/`blocked` statuses, strong secret hygiene.

---

## Pick-up directions for a new AI agent

1. **Read this file**, `/app/memory/PRD.md`, `/app/memory/AUDIT.md`, `/app/memory/CONTINUATION_PROMPT.md`.
2. Treat the existing repo as source of truth. **Never re-implement anything in §"Real / Working"** below.
3. Pick the top 2 P1/P2 items from PRD.md "Next actions" — that is your assignment.
4. Use the user's Gemini key (in `/app/backend/.env::GEMINI_API_KEY`) as **PRIMARY**. Emergent is fallback only. Minimise total LLM calls (per-min rate limit). `tier="light"` → flash, `tier="heavy"` → pro.
5. Always create a test in `/app/backend/tests/` for any new behaviour and update PRD.md + AUDIT.md before `finish`.

---

## Repository layout
```
/app
├── backend/
│   ├── server.py                  # FastAPI entrypoint + startup recovery sweep
│   ├── db.py                      # Mongo connection + indexes
│   ├── repositories.py            # All DB accessors
│   ├── orchestrator_models.py     # Pydantic models (Project, BRDRecord, etc.)
│   ├── event_ledger.py            # SSE + persisted event log
│   ├── state_machine.py           # Phase transitions
│   ├── engines/                   # PURE LOGIC, no FastAPI imports
│   │   ├── llm_gateway.py         # Gemini direct (primary) + Emergent (fallback) + tier routing
│   │   ├── brd_engine.py          # SME questions + structured derive
│   │   ├── architecture_engine.py # Deterministic classification + HIGH-1 unsupported propagation
│   │   ├── generation_engine.py   # Plan + per-file gen + 5 layers of deterministic fixups
│   │   ├── build_engine.py        # Real npm install/build + pip install/import
│   │   ├── repair_engine.py       # Classify → patch → retry, rollback on no-improvement
│   │   ├── snapshot_engine.py     # Pre-build snapshots for rollback
│   │   ├── acceptance_engine.py   # 15 honest checks + plan.endpoints verification (MEDIUM-1)
│   │   ├── export_engine.py       # Clean ZIP + manifest + secret scan
│   │   ├── constraints.py         # Phase 3b bounded customization registry
│   │   ├── improve_engine.py      # Phase 3a Improve/Fix (1 Pro call/request)
│   │   ├── ingest_engine.py       # Phase 4 ZIP/git ingest + BRD-from-code
│   │   └── recovery_engine.py     # Stale-pipeline sweep + manual recover
│   ├── routes/                    # Thin FastAPI wrappers around engines
│   │   ├── __init__.py            # Routes aggregator (all under /api prefix)
│   │   ├── projects.py            # CRUD + /recover endpoint
│   │   ├── brd.py
│   │   ├── architecture.py        # Override propagates `unsupported` to BRD (HIGH-1)
│   │   ├── plan.py
│   │   ├── generate.py            # Full pipeline (background asyncio task)
│   │   ├── build.py               # Manual build trigger (background asyncio task)
│   │   ├── acceptance.py
│   │   ├── export.py
│   │   ├── files.py
│   │   ├── events.py              # SSE + paged event list
│   │   ├── system.py              # /api/system/health
│   │   ├── constraints.py         # GET / PUT / POST reset
│   │   ├── improve.py             # POST/GET attempts
│   │   └── ingest.py              # /zip + /url + /status
│   ├── tests/                     # All checked-in tests live here
│   │   ├── test_high1_frontend_only_gating.py
│   │   ├── test_medium1_endpoint_verification.py
│   │   ├── test_improve_calculator_e2e.py  # 1 Pro call live test
│   │   └── test_phase4_ingest_e2e.py       # 1 Pro call live test
│   ├── poc/                       # Phase 1 POC (kept for regression)
│   └── .env                       # GEMINI_API_KEY + EMERGENT_LLM_KEY + MONGO_URL
├── frontend/
│   ├── src/
│   │   ├── App.js                 # Router + outlet context
│   │   ├── lib/
│   │   │   ├── api.js             # Single axios client + endpoint registry
│   │   │   └── useEventStream.js  # SSE hook
│   │   ├── components/
│   │   │   ├── cockpit/           # AppShell, EventLedgerDrawer, PhaseStepper, StatePill, StatusBadge
│   │   │   └── ui/                # shadcn/ui primitives
│   │   ├── pages/                 # ONE FILE PER PAGE — match url segment
│   │   │   ├── Dashboard.jsx      # + stuck-state badge on cards
│   │   │   ├── NewProject.jsx
│   │   │   ├── Cockpit.jsx        # + recovery banner
│   │   │   ├── BRD.jsx
│   │   │   ├── Architecture.jsx
│   │   │   ├── Plan.jsx
│   │   │   ├── Files.jsx
│   │   │   ├── Build.jsx          # + recovery banner
│   │   │   ├── Acceptance.jsx
│   │   │   ├── Export.jsx
│   │   │   ├── Constraints.jsx    # Phase 3b
│   │   │   ├── Improve.jsx        # Phase 3a
│   │   │   └── Ingest.jsx         # Phase 4 (backend wired; UI page exists)
│   │   ├── index.css              # Design tokens (electric cyan on graphite)
│   │   └── App.css
│   └── .env                       # REACT_APP_BACKEND_URL (do not change)
├── workspace/                     # Generated apps land here
│   └── projects/<project_id>/...
├── memory/                        # Persistent project knowledge
│   ├── REFERENCE.md               # ← you are here
│   ├── PRD.md                     # Live status + backlog
│   ├── AUDIT.md                   # Architecture audit + fixed/open issues
│   ├── CONTINUATION_PROMPT.md     # Stable prompt to resume work
│   ├── design_guidelines.md
│   └── test_credentials.md        # (none — no auth in this app)
├── test_reports/                  # Testing-agent reports
├── plan.md                        # Original product roadmap (Phases 1-5)
└── test_result.md                 # Test protocol + history
```

---

## Stack
- **Frontend**: React 19 (CRA + craco), Tailwind, shadcn/ui, framer-motion, lucide-react
- **Backend**: FastAPI 0.111, Motor, MongoDB (single db: `local_app_creator`)
- **LLM**: `google-genai 2.0` (primary, direct user key) + `emergentintegrations` (fallback)
- **Generated apps**: React 18 + Vite 5 (JS) + FastAPI + SQLAlchemy 2 + SQLite + Pydantic v2
- **Routing**: All backend routes prefixed `/api`. Frontend uses `REACT_APP_BACKEND_URL`.
- **Hot reload**: ON (both services). Edits to `engines/` or `routes/` will kill in-flight background tasks — see "Stuck pipeline" below.

---

## Key API endpoints (always `/api` prefixed)
| Surface          | Endpoint                                              | Notes                               |
|------------------|-------------------------------------------------------|-------------------------------------|
| Projects         | `POST/GET /projects` ; `GET/DELETE /projects/{id}`    |                                     |
|                  | `POST /projects/{id}/recover`                         | **Unstick orphaned pipelines**      |
| BRD              | `POST /projects/{id}/brd/questions ; /answers`         | `GET /brd`                          |
| Architecture     | `POST /projects/{id}/architecture/detect ; /override` | `GET`. Override → BRD `unsupported` |
| Plan             | `POST /projects/{id}/plan` ; `GET`                    |                                     |
| Generate         | `POST /projects/{id}/generate ; /run_full_pipeline`   | `GET /generate/status`              |
| Files            | `GET /projects/{id}/files ; /files/content`           |                                     |
| Build            | `POST /projects/{id}/build` ; `GET /builds`           |                                     |
| Acceptance       | `POST /projects/{id}/acceptance` ; `GET`              |                                     |
| Export           | `POST/GET /projects/{id}/export` + `/manifest` + `/download` |                              |
| Events           | `GET /projects/{id}/events` ; `/events/stream` (SSE)  |                                     |
| Constraints      | `GET/PUT /projects/{id}/constraints ; POST .../reset` | Phase 3b                            |
| Improve          | `POST/GET /projects/{id}/improve ; GET .../{attempt}` | Phase 3a                            |
| Ingest           | `POST /projects/ingest/zip ; /url ; GET /{id}/status` | Phase 4                             |
| System           | `GET /system/health`                                  | LLM provider + tier_models          |

---

## Key Mongo collections
- `projects` (UUID id, unique)
- `brds`, `architectures`, `plans` (unique per project_id)
- `builds`, `acceptance`, `exports`, `events`, `runs` (multi)
- `constraints` (unique per project_id)
- `improve_attempts` (compound unique project_id + attempt_id)

---

## Real / Working capabilities (do NOT re-implement)
- BRD engine — SME questions + structured derive + maturity
- Architecture detection + gating + override with **HIGH-1**: limited_prototype propagates `status="unsupported"` onto backend-dependent BRD requirements
- Plan generation (file-by-file)
- Full-stack generation with 5 layers of deterministic fixups
- Real build engine (npm install/build + pip install/import)
- Repair engine (classify → patch → retry, rollback on no-improvement, constraint-respecting)
- Snapshot/rollback
- Acceptance engine — 15 honest checks + requirement coverage + `UNSUPPORTED` honoring + **MEDIUM-1** plan.endpoints[*].path verified against backend source
- Export with clean ZIP + manifest + secret scan
- Event ledger + SSE
- **Phase 3a Improve/Fix** — live-verified 2026-02-13 (1 Pro call/request)
- **Phase 3b Constraints registry** — engine + CRUD + repair integration + UI
- **Phase 4 Ingest** — ZIP upload + git URL clone + 1-Pro-call BRD-from-code (live-verified 2026-02-13)
- **Stuck-pipeline recovery** — startup sweep + `POST /projects/{id}/recover` + UI banners (Cockpit, Build, Dashboard)
- Hybrid LLM tier routing: `tier="light"` → Flash, `tier="heavy"` → Pro

---

## Stuck pipeline / "Build does nothing" troubleshooting
When the backend hot-reloads (or crashes) during an in-flight `_run_pipeline`, `_do_build`, or `_derive_brd_background` task, the project freezes in `state ∈ {Generating, Building, Repair, Acceptance}` with `last_build_status=null`.

**Auto-recovery** runs on every backend startup (`engines/recovery_engine.py::sweep_stale_pipelines`). It emits a `pipeline.aborted` event and resets state to the safest prior checkpoint.

**Manual recovery**: hit `POST /api/projects/{id}/recover` or click the "Recover" button on the Cockpit / Build page.

Common cause during dev: editing files in `engines/` or `routes/` triggers WatchFiles → uvicorn reload → background tasks die. Either avoid edits during a pipeline run, or just hit Recover after.

---

## How to run a real Improve/Fix or Ingest E2E test (1 Pro call)
```
cd /app/backend
python tests/test_improve_calculator_e2e.py        # 1 Pro call
python tests/test_phase4_ingest_e2e.py             # 1 Pro call
```

## How to run unit tests (no LLM)
```
cd /app/backend
python tests/test_high1_frontend_only_gating.py
python tests/test_medium1_endpoint_verification.py
```

---

## Common platform commands
```
sudo supervisorctl status                          # service health
sudo supervisorctl restart backend                 # only after .env change or new pip install
tail -n 80 /var/log/supervisor/backend.err.log    # backend logs
curl -s http://localhost:8001/api/system/health    # provider + tier_models check
```

---

## Things to NEVER do
- Don't rewrite `requirements.txt`, `package.json`, or `.env` files wholesale.
- Don't change `MONGO_URL`, `DB_NAME`, or `REACT_APP_BACKEND_URL`.
- Don't add fake/mock paths to engines — the platform's whole value is honest reporting.
- Don't write secret values into any generated file.
- Don't add Emergent SDK installations for LLMs you can reach via `LLMGateway` (gateway abstracts both).
