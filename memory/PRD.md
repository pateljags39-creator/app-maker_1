# Local App Creator — Product Requirements Document

## Original problem statement (verbatim intent)
Continue building **Local App Creator** — a local-first AI software-engineering platform that:
- creates apps from BRDs via SME-style questioning,
- detects architecture and **gates invalid combos**,
- generates a full-stack (React + Vite + FastAPI + SQLite) scaffold,
- runs **real** npm + pip builds, repairs failures within a bounded patch budget,
- supports **Improve/Fix** workflow with bounded customization + snapshot/rollback,
- ingests existing projects for rework (Phase 4),
- exports clean, secret-free ZIPs with manifests,
- is honest (no fake APIs, no silent fallbacks, explicit `unsupported`/`blocked` statuses).

Source repo: `pateljags39-creator/app-maker_1` @ main, cloned into `/app`.

LLM backbone: **Google Gemini** (Flash for light tasks, Pro for heavy). User-supplied
`GEMINI_API_KEY`. Emergent universal key wired as fallback. **Minimise LLM calls** —
per-minute rate limit.

## Stack
- Frontend: React 19 (CRA + craco), Tailwind, shadcn, framer-motion
- Backend: FastAPI 0.111, Motor, MongoDB (`local_app_creator`)
- LLM gateway: `google-genai` 2.0 primary + `emergentintegrations` fallback
- Generated stack contract: React 18 + Vite 5 + FastAPI + SQLAlchemy 2 + SQLite + Pydantic v2
- Workspace storage: `/app/workspace/projects/<id>/`

## Implementation status (current)

### Real / Working
- BRD engine (SME questions + structured derive + maturity)
- Architecture detection + gating + **override with limited_prototype propagating `unsupported` to BRD requirements (HIGH-1, fixed 2026-02)**
- Plan generation (file-by-file)
- Full-stack generation with 5 layers of deterministic fixups
- Real build engine (npm install/build + pip install/import)
- Repair engine (classify → patch → retry, rollback on no-improvement, constraint-respecting)
- Snapshot/rollback
- Acceptance engine (15 checks + requirement coverage; **now honors `status=unsupported`**)
- Export with clean ZIP + manifest + secret scan
- Event ledger + SSE
- Phase 3a: **Improve/Fix workflow** end-to-end (snapshot → 1 Pro call → constraint validate → atomic apply → real rebuild → auto-rollback on regression → re-acceptance). **Live-verified 2026-02-13** with a tiny calculator workspace: rolled_back path fired correctly when build regressed PASS → PARTIAL.
- Phase 3b: **Bounded-customization constraints registry** (engine + CRUD routes + Mongo + repair-engine integration + Constraints UI)
- Phase 4 (partial): `ingest_engine.py` + `routes/ingest.py` scaffolded (632/254 LoC) — not exercised end-to-end yet
- Hybrid LLM tier routing: `tier="light"` → Flash, `tier="heavy"` → Pro

### Missing / Backlog
- **P1 — Phase 4 Rework/Ingest E2E verification**: live test of ZIP upload / git URL → BRD-from-code → architecture → Improve unlock
- **P2 — MEDIUM-1**: acceptance engine should verify `plan.endpoints[*].path` exists in generated `backend/main.py`
- **P2 — MEDIUM-2**: per-project configurable repair retry budget (currently hard-coded at 2)
- **P2 — Phase 5**: internal component-library lookup / resource discovery
- **P3 — LOW-1**: 6× react-hooks/exhaustive-deps warnings (Acceptance/Architecture/BRD/Build/Export/Plan)
- **P3 — LOW-2**: requirements.txt trim (currently a wide `pip freeze` with ~130 pins)
- **P3 — LOW-3**: build `overall_status` returns `null` in some API paths (cosmetic; UI compensates)

## Architecture audit
Full architecture audit at `/app/memory/AUDIT.md` (last updated 2026-02-13).

## Key APIs (per-project, all prefixed with `/api`)
- `POST /api/projects` ; `GET /api/projects` ; `GET/DELETE /api/projects/{id}`
- `POST /api/projects/{id}/brd/questions` ; `/answers` ; `GET /brd`
- `POST /api/projects/{id}/architecture/detect` ; `/override` ; `GET ...`
- `POST /api/projects/{id}/plan` ; `GET ...`
- `POST /api/projects/{id}/generate` ; `/generate/status`
- `GET /api/projects/{id}/files` ; `/files/content?path=...`
- `POST /api/projects/{id}/build` ; `GET /builds`
- `POST /api/projects/{id}/acceptance` ; `GET ...`
- `POST /api/projects/{id}/export` ; `/manifest` ; `/download`
- `GET /api/projects/{id}/events` ; `/events/stream` (SSE)
- `GET/PUT /api/projects/{id}/constraints` ; `POST .../reset`
- `POST/GET /api/projects/{id}/improve` ; `GET /improve/{attempt_id}`
- `POST /api/projects/{id}/ingest/zip` ; `/ingest/url` (Phase 4 scaffolded)
- `GET /api/system/health`

## Key DB collections
- `projects` (UUID id), `brds`, `architectures`, `plans`, `builds`, `acceptance`, `exports`, `events`, `runs`, `constraints` (unique on project_id), `improve_attempts` (compound unique project_id+attempt_id)

## Credentials
- `GEMINI_API_KEY` (user-supplied; in `backend/.env`)
- `EMERGENT_LLM_KEY` (fallback; in `backend/.env`)

## Test artifacts
- `/app/backend/tests/test_improve_calculator_e2e.py` — live Improve E2E (1 Pro call)
- `/app/backend/tests/test_high1_frontend_only_gating.py` — HIGH-1 unit tests (3 cases)
- `/app/backend_test.py` — earlier Phase 2 acceptance harness
- `/app/test_reports/iteration_1.json` — Phase 2 testing agent report

## Recent changelog
- **2026-02-13**: HIGH-1 fix — `architecture_engine.detect_architecture` now returns
  `unsupported_requirement_indices` + `unsupported_signal_keywords` when limited_prototype
  is accepted on a backend-dependent BRD. `routes/architecture.override` propagates these
  onto the BRD itself as `status="unsupported"` + `unsupported_reason`. `acceptance_engine`
  records them as `UNSUPPORTED` (not weak coverage) and emits a dedicated info check.
- **2026-02-13**: Live Improve/Fix E2E verified on tiny calculator workspace — 1 Pro call,
  manifest validated, applied, rebuilt, regression detected (PASS → PARTIAL), auto-rollback
  succeeded, attempt persisted.
- Prior pass: CRITICAL-1 (requirements.txt pydantic/google-genai conflict) + CRITICAL-2
  (hybrid LLM tier routing) + Phase 3a + Phase 3b shipped.

## Next actions (prioritised)
1. **P1** Phase 4 — exercise ingest end-to-end (small ZIP or tiny public repo) to confirm
   workspace staging + BRD-from-code + architecture detect path.
2. **P2** MEDIUM-1 endpoint↔requirement verification in acceptance.
3. **P2** Surface repair retry budget as a project setting (MEDIUM-2).
4. **P3** Polish: react-hooks deps warnings, requirements.txt trim.
