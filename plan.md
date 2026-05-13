# plan.md — Local App Creator (Local-first AI Software Factory)

## 1) Objectives
- Prove the **core hypothesis**: given a structured BRD, the system can generate a **working full-stack app** (React+Vite + FastAPI + SQLite), validate builds, and **repair** failures with bounded patches.
- Build the **Orchestrator (control plane)** that:
  - collects/derives BRDs via SME-style questions,
  - detects architecture and blocks invalid paths,
  - generates projects into `/app/workspace/projects/<project_id>/`,
  - runs real build/acceptance checks, snapshots, and exports clean ZIPs,
  - presents a premium UX with an **event ledger** and honest PASS/PARTIAL/FAIL signals.
- Maintain non‑negotiables: no fake APIs, no silent fallbacks, explicit placeholders, strong secret hygiene.

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
  - Uses hardcoded BRD JSON (notes CRUD) → architecture detection (`full_stack`).
  - Generates a file plan → generates files for frontend+backend+README.
  - Writes to `/app/workspace/projects/poc-<ts>/`.
  - Runs real validations:
    - backend: venv-free `pip install -r requirements.txt` + `python -c "import main"` (or `uvicorn` import check)
    - frontend: `npm install` + `npm run build`.
  - On failure: capture stderr/stdout → LLM patch request (single file per patch) → apply → retry (max 2).
  - Runs acceptance probes: backend has `/api/notes` GET/POST; frontend `dist/` exists.
  - Exports ZIP with forbidden-globs filter + manifest.
- Add minimal shared utilities used by POC (and later app):
  - `engines/llm_gateway.py`, `engines/build_engine.py`, `engines/repair_engine.py`, `engines/export_engine.py`, `engines/snapshot_engine.py`.
- Websearch (best practice) before finalizing build runner + safe patch boundaries:
  - running npm/pip builds safely in containers
  - typical Gemini structured JSON prompting + retry patterns
- Iterate until POC success criteria met (no proceeding otherwise).

**Phase 1 Success Criteria**
- Within 2 repair retries, generated app:
  - backend imports cleanly and exposes required routes,
  - frontend builds and produces `dist/`,
  - export ZIP is produced and verified clean.

---

### Phase 2 — V1 Orchestrator App (backend + premium UI) built around proven core

**Phase 2 User Stories**
1. As a user, I can create a project from an idea and see it appear on the dashboard.
2. As a user, I answer SME-style questions and watch BRD maturity increase.
3. As a user, I see architecture classification and the system blocks invalid combos unless I explicitly accept a limited prototype.
4. As a user, I trigger generation and can browse the generated file tree and contents.
5. As a user, I can run build + see logs + repair attempts + final status honestly.
6. As a user, I can export a clean ZIP and view the export manifest.

**Backend (FastAPI + Mongo) — real orchestrator core**
- Implement Mongo collections: `projects`, `runs`, `events`, `brds`, `architectures`, `plans`, `build_records`, `repair_records`, `snapshots`, `exports`, `acceptance_results`.
- Implement engines (real modules, minimal but functional):
  - `brd_engine`: question set + requirement extraction + maturity score + missing-info flags.
  - `architecture_engine`: classify + reasoning + block rules.
  - `plan_engine`: file list + constraints + per-file goals.
  - `generation_engine`: file-by-file generation using LLM gateway and schema validation.
  - `build_engine`, `repair_engine`, `snapshot_engine`, `acceptance_engine`, `export_engine`.
- Add event ledger + SSE:
  - emit events for every major step (state change, plan, file write, build start/end, repair attempt, export).
  - `/api/projects/:id/events` (paged) + `/api/projects/:id/events/stream` (SSE).
- API surface (MVP):
  - `POST /api/projects`, `GET /api/projects`, `GET /api/projects/{id}`
  - `POST /api/projects/{id}/brd/questions`, `POST /api/projects/{id}/brd/answers`, `GET /api/projects/{id}/brd`
  - `POST /api/projects/{id}/architecture/detect`, `POST /api/projects/{id}/architecture/override`
  - `POST /api/projects/{id}/plan`
  - `POST /api/projects/{id}/generate` (background task)
  - `GET /api/projects/{id}/files`, `GET /api/projects/{id}/files/content?path=...`
  - `POST /api/projects/{id}/build`, `GET /api/projects/{id}/builds`
  - `POST /api/projects/{id}/acceptance`, `GET /api/projects/{id}/acceptance`
  - `POST /api/projects/{id}/export`, `GET /api/projects/{id}/export`
  - `GET /api/system/health` (LLM provider health + config sanity)

**Frontend (React + shadcn/tailwind) — “software factory cockpit”**
- Before building pages: run design pass (layout, typography, state badges, logs viewer, empty/error states).
- Build pages (MVP): Dashboard, New Project, Project Cockpit, BRD, Architecture, Plan, Files, Build+Repairs, Acceptance, Export.
- Implement SSE event panel (right drawer) + status badges (Real/Partial/Unsupported/Blocked/Placeholder).

**Phase 2 Testing (mandatory)**
- One full E2E run: create project → BRD answers → architecture → generate → build → acceptance → export.
- Call testing agent after Phase 2 implementation and fix failures.

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
- Expanded repair taxonomy.
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
- Resource discovery pipeline (staged → reviewed → promoted).
- Acceptance suite coverage expansion.
- UI polish pass + final testing agent round.

---

## 3) Next Actions (immediate)
1. Create workspace dir structure: `/app/workspace/projects/`.
2. Implement Phase 1 POC modules + `test_core.py` and run it until PASS.
3. Add backend env handling: Gemini primary key + fallback (backend-only), never emitted.
4. Once Phase 1 PASS is stable, start Phase 2 orchestrator backend endpoints, then frontend cockpit.

---

## 4) Success Criteria
- Phase 1: POC reliably generates + builds + repairs (≤2 retries) + exports a clean ZIP with manifest.
- Phase 2: Orchestrator supports full flow with real event ledger + SSE, honest acceptance, and downloadable exports.
- Phase 3+: Improve/fix, bounded customization, rework, and discovery features ship incrementally with snapshots/rollback and repeated testing-agent validation.
