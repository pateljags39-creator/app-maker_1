# plan.md — Local App Creator (Local-first AI Software Factory)

## 1) Objectives
- Prove the **core hypothesis**: given a structured BRD, the system can generate a **working full-stack app** (React+Vite + FastAPI + SQLite), validate builds, and **repair** failures with bounded patches.
- Build the **Orchestrator (control plane)** that:
  - collects/derives BRDs via SME-style questions,
  - detects architecture and blocks invalid paths,
  - generates projects into `/app/workspace/projects/<project_id>/`,
  - runs real build/acceptance checks, snapshots, and exports clean ZIPs,
  - presents a premium UX with a **real-time event ledger** (SSE) and honest PASS/PARTIAL/FAIL signals.
- Maintain non‑negotiables: **no fake APIs**, **no silent fallbacks**, explicit placeholders, strong secret hygiene.

**Current status (this sprint):**
- Phase 1 POC is **complete** and passes reliably.
- Phase 2 Orchestrator backend + premium cockpit UI is **implemented** and running.
- Next objective: **end-to-end validation via testing_agent_v3** across all Phase 2 user stories.

---

## 2) Implementation Steps

### Phase 1 — Core POC (isolation): full-stack generation + build/repair + export
**Goal:** do not start the UI app until this passes reliably.

**POC User Stories**
1. As a user, I can provide a tiny BRD JSON and get a runnable full-stack scaffold.
2. As a user, I see architecture classified as full_stack with reasoning.
3. As a user, when builds fail, the system attempts safe file-scoped repairs with a retry budget.
4. As a user, I get an export ZIP that is clean (no node_modules, no .env/secrets, no caches).
5. As a user, I get an honest final verdict (PASS/PARTIAL/FAIL) with reasons.

**Steps**
- Create `/app/backend/poc/test_core.py` that:
  - Initializes LLM gateway: **primary direct Gemini key** → fallback to **Emergent universal key** on quota/429.
  - Uses notes CRUD BRD → architecture detection (`full_stack`).
  - Generates a file plan → generates files for frontend+backend+README.
  - Writes to `/app/workspace/projects/poc-<ts>/`.
  - Runs real validations:
    - backend: `pip install -r requirements.txt` + `python -c "import main"`
    - frontend: `npm install` + `npm run build`.
  - On failure: capture stderr/stdout → LLM patch request (single file per patch) → apply → retry (max 2) with rollback on non-improvement.
  - Runs acceptance checks + export ZIP with manifest + secret scrub.
- Add minimal shared utilities used by POC (and later app):
  - `engines/llm_gateway.py`, `engines/generation_engine.py`, `engines/build_engine.py`, `engines/repair_engine.py`, `engines/export_engine.py`, `engines/snapshot_engine.py`, `engines/acceptance_engine.py`.

**Phase 1 Success Criteria**
- Within 2 repair retries, generated app:
  - backend imports cleanly and exposes required routes,
  - frontend builds and produces `dist/`,
  - export ZIP is produced and verified clean.

**Status (Completed)**
- ✅ POC completed successfully and reliably:
  - BUILD=PASS, ACCEPTANCE=PASS, EXPORT=OK **twice in a row**.
  - Verified primary Gemini quota handling: automatic fallback to Emergent key.
  - Improved generation reliability:
    - switched file generation to plaintext,
    - added deterministic post-fixups (backend imports/Base rules + dependency scanning).

---

### Phase 2 — V1 Orchestrator App (backend + premium UI) built around proven core

**Phase 2 User Stories**
1. As a user, I can create a project from an idea and see it appear on the dashboard.
2. As a user, I answer SME-style questions and watch BRD maturity increase.
3. As a user, I see architecture classification and the system blocks invalid combos unless I explicitly accept a limited prototype.
4. As a user, I trigger generation and can browse the generated file tree and contents.
5. As a user, I can run build + see logs + repair attempts + final status honestly.
6. As a user, I can export a clean ZIP and view the export manifest.
7. As a user, I can see a **real-time event ledger** of everything happening.

**Backend (FastAPI + Mongo) — real orchestrator core**
- Implemented Mongo persistence and indexes:
  - Collections: `projects`, `events`, `brds`, `architectures`, `plans`, `builds`, `acceptance`, `exports`.
  - Modules: `/app/backend/db.py`, `/app/backend/repositories.py`, `/app/backend/orchestrator_models.py`.
- Implemented engines (real modules, functional):
  - `engines/llm_gateway.py` (Gemini direct primary + Emergent fallback)
  - `engines/brd_engine.py`
  - `engines/architecture_engine.py`
  - `engines/generation_engine.py` (LLM plan + file generation + deterministic post-fixups for imports/Base + frontend/backend dependency scanning)
  - `engines/build_engine.py` (real npm + pip builds)
  - `engines/repair_engine.py` (safe single-file patching, retry budget, rollback)
  - `engines/snapshot_engine.py`
  - `engines/acceptance_engine.py` (honest PASS/PARTIAL/FAIL checks + requirement coverage)
  - `engines/export_engine.py` (clean ZIP + manifest + secret scan)
- Event ledger + SSE:
  - In-process pub/sub with persistent event storage: `/app/backend/event_ledger.py`
  - Endpoints: `/api/projects/{id}/events` (paged) + `/api/projects/{id}/events/stream` (SSE)
- State machine:
  - `/app/backend/state_machine.py` enforcing allowed lifecycle transitions.
- API surface (implemented):
  - `POST /api/projects`, `GET /api/projects`, `GET /api/projects/{id}`, `DELETE /api/projects/{id}`
  - `POST /api/projects/{id}/brd/questions`, `POST /api/projects/{id}/brd/answers`, `GET /api/projects/{id}/brd`
  - `POST /api/projects/{id}/architecture/detect`, `POST /api/projects/{id}/architecture/override`, `GET /api/projects/{id}/architecture`
  - `POST /api/projects/{id}/plan`, `GET /api/projects/{id}/plan`
  - `POST /api/projects/{id}/generate`, `GET /api/projects/{id}/generate/status` (background pipeline)
  - `GET /api/projects/{id}/files`, `GET /api/projects/{id}/files/content?path=...`
  - `POST /api/projects/{id}/build`, `GET /api/projects/{id}/builds`
  - `POST /api/projects/{id}/acceptance`, `GET /api/projects/{id}/acceptance`
  - `POST /api/projects/{id}/export`, `GET /api/projects/{id}/export`, `GET /api/projects/{id}/export/manifest`, `GET /api/projects/{id}/export/download`
  - `GET /api/system/health` (LLM provider health + model)
- Server entrypoint:
  - `/app/backend/server.py` is the orchestrator entrypoint; confirms **32 routes registered**.
  - Health endpoint live; CRUD verified via `curl`.

**Frontend (React + shadcn/tailwind) — “software factory cockpit”**
- Design pass completed and saved to: `/app/memory/design_guidelines.md`
- Implemented premium cockpit shell:
  - Dark graphite + electric cyan palette; IBM Plex Sans/Mono typography.
  - `AppShell` with sidebar nav, top bar (project info + state pill), system health pill, and event ledger right drawer.
  - Real-time SSE event feed with pause/clear/filter.
- Implemented 10 pages:
  1. Dashboard
  2. New Project
  3. Cockpit (PhaseStepper + quick stats + recent activity)
  4. BRD (questions + maturity gauge + requirements)
  5. Architecture (detect + override + limited prototype gate)
  6. Plan (plan tree + endpoints + entities)
  7. Files (file tree + code viewer)
  8. Build (runs + step details + repair timeline)
  9. Acceptance (checks matrix + requirement coverage)
  10. Export (ZIP + manifest + secret scan)
- Verified renders correctly at preview URL.

**Phase 2 Testing (mandatory)**
- Run full E2E testing via `testing_agent_v3` covering Phase 2 user stories.
- Notes for testing agent:
  - Generation pipeline can take **~2–3 minutes** per run (LLM + npm + pip + build + repair).
  - Testing should include appropriate waits/polling for state transitions and event stream updates.

**Status (Implemented; requires testing confirmation)**
- ✅ Backend implemented and running.
- ✅ Frontend implemented and compiling.
- ⏭️ Next: testing_agent_v3 end-to-end validation; fix any issues it reports.

---

### Phase 3 — Improve/Fix + bounded customization (safe patch workflow)

**Phase 3 User Stories**
1. As a user, I can submit feedback (“bug/feature request”) against a generated project.
2. As a user, I see a proposed patch plan + file list before changes apply.
3. As a user, changes are bounded to allowed paths and snapshotted before applying.
4. As a user, the system rebuilds and rolls back automatically on regression.
5. As a user, I can export the improved app with updated manifest.

**Scope**
- `/api/projects/{id}/improve`: feedback → plan → approval gate (optional) → patch → rebuild → acceptance.
- Diff viewer + patch approvals UI.
- Snapshot-before-patch and rollback-on-regression are mandatory.
- Testing agent round.

---

### Phase 4 — Repair deepening + Rework existing projects

**Phase 4 User Stories**
1. As a user, I can upload an existing project ZIP for analysis.
2. As a user, I receive a rework BRD + gap report.
3. As a user, I can apply an enhancement plan with snapshots and rollback.
4. As a user, the system classifies build failures and shows specific repair actions taken.
5. As a user, exports remain clean and reproducible.

**Scope**
- ZIP ingest → safe unzip → forbidden-file filtering → workspace staging.
- Rework engine: analyze → propose plan → apply → rebuild.
- Expanded repair taxonomy and richer repair records.
- Testing agent round.

---

### Phase 5 — Resource discovery + acceptance hardening + polish

**Phase 5 User Stories**
1. As a user, I can discover/import a component/template with license + metadata gates.
2. As a user, templates are only applied when they fit my BRD (no forced mismatch).
3. As a user, acceptance checks explain what is missing/unsupported.
4. As a user, I can trust exports never include secrets or build artifacts.
5. As a user, the UI feels premium (keyboard shortcuts, command palette, consistent states).

**Scope**
- Resource discovery pipeline (staged → reviewed → promoted) with license + forbidden-file filtering.
- Acceptance suite coverage expansion (architecture fit, requirement coverage, placeholder honesty, export hygiene, secret hygiene).
- UI polish: command palette, keyboard shortcuts, empty/loading/error refinements.
- Testing agent final round.

---

## 3) Next Actions (immediate)
1. Run **testing_agent_v3** across all Phase 2 user stories (E2E) and capture failures in `test_result.md`.
2. Fix any issues found (API edge cases, SSE reconnection, UI state mismatches, pipeline timing).
3. Once Phase 2 tests pass, begin Phase 3 (Improve/Fix + bounded customization + diff/approval UI).

---

## 4) Success Criteria
- Phase 1: POC reliably generates + builds + repairs (≤2 retries) + exports a clean ZIP with manifest. ✅ Completed.
- Phase 2: Orchestrator supports full flow with real event ledger + SSE, honest acceptance, and downloadable exports. **Implemented; pending testing confirmation.**
- Phase 3+: Improve/fix, bounded customization, rework, and discovery features ship incrementally with snapshots/rollback and repeated testing-agent validation.
