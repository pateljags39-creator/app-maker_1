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
- Acceptance engine (15 checks + requirement coverage; **honors `status=unsupported`**; **MEDIUM-1: verifies plan.endpoints[*].path against backend source**)
- Export with clean ZIP + manifest + secret scan
- Event ledger + SSE
- Phase 3a: **Improve/Fix workflow** end-to-end (live-verified 2026-02-13)
- Phase 3b: **Bounded-customization constraints registry**
- **Phase 4: Rework/Ingest existing project (live-verified 2026-02-13)** — ZIP upload → safe extract → stack detect → deterministic architecture → endpoint scan → 1-Pro-call BRD-from-code with honest `implemented/partial/unsupported` markers
- Hybrid LLM tier routing: `tier="light"` → Flash, `tier="heavy"` → Pro

### Missing / Backlog
- **P2 — MEDIUM-2**: per-project configurable repair retry budget (currently hard-coded at 2)
- **P2 — Phase 5**: internal component-library lookup / resource discovery
- **P2 — Phase 4 polish**: surface ingest UI page (current implementation is backend-only)
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
- **2026-05-13 (continuation pass — user-reported "calculator made a mess" bug)**:
  - **HIGH-2 fixed — Stale package-lock.json broke every project where the deterministic
    deps-fixup added a dep after first build.** `build_engine.build_frontend` was using
    `npm ci` whenever `package-lock.json` existed, but the deterministic fixup
    `generation_engine._ensure_frontend_deps` writes/updates `package.json` *after*
    a previous install ran (or after the LLM forgets to declare an imported package),
    leaving the lockfile stale. `npm ci` refuses to update a stale lockfile, so the
    next `vite build` failed with `Rollup failed to resolve import "uuid"` (or any
    similar package). Root cause confirmed by inspecting workspace
    `a6ed1376e046` (Web Calculator Pro) — build logs show 2 consecutive
    `Rollup failed to resolve import "uuid"` failures even though `uuid` was correctly
    listed in `package.json`. Fix: build engine now treats a lock as "fresh" only if
    (mtime ≥ package.json mtime − 1s) AND (every declared dep appears in the lock).
    Otherwise the stale lock is deleted and `npm install` regenerates it. Manual
    rebuild of the failing calculator workspace now passes (`✓ 109 modules transformed`).
    Unit tests at `tests/test_high2_stale_lockfile_fallback.py` cover all 4 cases.

  - **Stuck-pipeline recovery shipped** (Issue 1 from user). New `engines/recovery_engine.py`
    with `sweep_stale_pipelines()` (called on FastAPI startup; reverts any project in
    `Generating/Building/Repair/Acceptance` older than 90s to its safest prior checkpoint
    and emits `pipeline.aborted` event) and `manual_recover(project_id)` (exposed via
    `POST /api/projects/{id}/recover`). Frontend wires a recovery banner on Cockpit + Build
    pages and a "stuck · recover" badge on Dashboard cards. Tested: both previously stuck
    user projects (`a2a7b1c77270`, `a6ed1376e046`) auto-recovered to `Plan` on the next
    backend boot. 4 unit tests in `tests/test_recovery_engine.py` all pass.
  - **Master reference doc** created at `/app/memory/REFERENCE.md` — single entry point
    for any AI agent to find pick-up directions, repo layout, API map, Mongo schema,
    "Real / Working" list, and stuck-pipeline troubleshooting.
- **2026-02-13 (later in same session)**: 
  - **MEDIUM-1 shipped** — `acceptance_engine.run_acceptance` now accepts an optional
    `plan` argument; when a plan is provided, every `plan.endpoints[*].path` is searched
    in `backend/**/*.py` (handles `APIRouter(prefix='/api')` by also matching the
    prefix-stripped form). Missing endpoints surface as a PARTIAL
    `plan.endpoints_implemented` check with the full missing list. All 4 call sites
    (`routes/acceptance.py`, `routes/build.py`, `routes/generate.py`,
    `engines/improve_engine.py`) updated. Back-compat: no plan → check skipped.
  - **Phase 4 ingest E2E verified live** — built a tiny in-memory ZIP (Vite+React +
    FastAPI notes app, in-memory storage), uploaded via `/api/projects/ingest/zip`,
    polled until `ingest_status=complete`. Result: project landed in
    `state=Architecture`, architecture correctly detected as `api_driven` (honest —
    no DB present), plan synthesized 3 endpoints (`GET/POST /notes`,
    `DELETE /notes/{note_id}`), and BRD-from-code (1 Pro call) returned 5
    honestly-classified requirements including 2 `unsupported` markers for
    persistence-related features that the source code doesn't actually implement.
  - Confirmed direct Gemini is primary; Emergent fallback never triggered.
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
1. **P2** Surface ingest in the cockpit UI (an `Ingest.jsx` page with ZIP-drop + URL form, wired into the sidebar between Dashboard and New Project).
2. **P2** MEDIUM-2 — surface repair retry budget as a per-project setting (currently hard-coded at 2).
3. **P2** Phase 5 — internal component-library lookup / resource discovery.
4. **P3** Polish: 6× react-hooks/exhaustive-deps warnings, requirements.txt trim, `build.overall_status=null` cosmetic.
5. **P3** "Preview diff before apply" toggle on Improve/Fix UI (cache the manifest from the 1 Pro call, render diff, gate `_apply()` behind explicit accept — would eliminate wasted rebuilds for rejected manifests).
