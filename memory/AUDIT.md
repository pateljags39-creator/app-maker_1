# Local App Creator — Architecture Audit

**Scope:** Repository `pateljags39-creator/app-maker_1` @ `main`, cloned into `/app`.
**Audit date:** 2026-05-13.
**Audited by:** Continuation pass (no greenfield rewrite).
**Method:** Read-only inspection of every backend engine + route, every frontend page +
shell, two prior generated workspaces, prior `test_reports/iteration_1.json`, and a
live `pip install --dry-run` + service smoke test.

---

## 1. Architecture Audit

### 1.1 What this repo actually is

The platform is a **Phase-2-complete software-factory cockpit**, not a template
generator. It is a real local-first AI engineering pipeline whose generated apps
have been verified to be real React+Vite+FastAPI+SQLite scaffolds (confirmed by
inspecting `/app/workspace/projects/6c7ac7efd2c4` and `…/b2aea88668c4` — both
contain working `backend/main.py`, `frontend/vite.config.js`, etc.).

```
┌──────────────────────── Platform stack ────────────────────────┐
│  React 19 (CRA + craco) + Tailwind/shadcn + framer-motion      │  ← cockpit UI
│  FastAPI 0.111 + Motor (Mongo)                                 │  ← orchestrator API
│  MongoDB (single db: local_app_creator)                        │  ← project/event/build state
│  google-genai 2.0 (primary) + emergentintegrations (fallback)  │  ← LLM gateway
│  /app/workspace/projects/<id>/ (filesystem)                    │  ← generated app storage
└────────────────────────────────────────────────────────────────┘

Generated stack (fixed contract):
   React 18 + Vite 5 (JS) + FastAPI + SQLAlchemy 2 + SQLite + Pydantic v2
```

### 1.2 Module map (backend)

| Module                                  | Purpose                                                        | Quality   |
|-----------------------------------------|----------------------------------------------------------------|-----------|
| `engines/llm_gateway.py`                | Direct Gemini primary + Emergent fallback, quota-detection     | Solid     |
| `engines/brd_engine.py`                 | SME-style question gen + structured BRD derive                 | Solid     |
| `engines/architecture_engine.py`        | Deterministic classification + LLM hint + blocked-combo logic  | Solid     |
| `engines/generation_engine.py`          | Plan → per-file generation + 5 layers of deterministic fixups  | Strong    |
| `engines/build_engine.py`               | Real `npm install/build` + `pip install/import` with timeouts  | Solid     |
| `engines/repair_engine.py`              | Classify → LLM patch → apply → rebuild → rollback-on-no-gain   | Strong    |
| `engines/acceptance_engine.py`          | Honest PASS/PARTIAL/FAIL checks + requirement coverage         | Solid     |
| `engines/snapshot_engine.py`            | Pre-build snapshot for rollback                                | Solid     |
| `engines/export_engine.py`              | Clean ZIP + manifest + **secret scan**                         | Solid     |
| `event_ledger.py` + `routes/events.py`  | SSE stream + persisted ledger                                  | Solid     |
| `state_machine.py`                      | Phase transitions (BRD→Architecture→Plan→…→Export)             | Solid     |
| `repositories.py` + `db.py`             | Mongo accessors, UUID-only ids                                 | Solid     |
| Routes: `brd`, `architecture`, `plan`,  | Thin orchestration wrappers around engines                     | Clean     |
| `generate`, `build`, `files`,           |                                                                |           |
| `acceptance`, `export`, `projects`,     |                                                                |           |
| `events`, `system`                      |                                                                |           |

### 1.3 Module map (frontend)

| Page                  | Status     | Notes                                                              |
|-----------------------|------------|--------------------------------------------------------------------|
| `Dashboard.jsx`       | Working    | Polls `/api/projects`. State pills. Reports `API offline` on fail. |
| `NewProject.jsx`      | Working    | Per prior test report.                                             |
| `Cockpit.jsx`         | Working    | PhaseStepper, run-full-pipeline button, live SSE mini-feed.        |
| `BRD.jsx`             | Working    | Question form + answer submit + maturity readout.                  |
| `Architecture.jsx`    | Working    | Decision + reasoning + override.                                   |
| `Plan.jsx`            | Working    | File-level plan view.                                              |
| `Files.jsx`           | Working    | Tree + code viewer. Validated with FastAPI scaffold.               |
| `Build.jsx`           | Working    | Build history + repair attempts timeline.                          |
| `Acceptance.jsx`      | Working    | Matrix table + requirement coverage.                               |
| `Export.jsx`          | Working    | ZIP download + manifest + secret-scan banner.                      |
| `EventLedgerDrawer`   | Working    | SSE drawer, filter tabs (all/info/success/warning/error).          |

Frontend warnings observed at compile:
- 6× `react-hooks/exhaustive-deps` warnings on `useEffect` polling loops
  (Acceptance, Architecture, BRD, Build, Export, Plan). Non-blocking; pages still
  render & poll correctly because `load` is stable inside the closures. Tracked as
  Low-priority follow-up (not silently fixed in this pass).

---

## 2. Implementation Status Matrix

Mapped against the BRD's product modules.

| BRD Capability                                     | Status         | Evidence / Notes                                                                    |
|----------------------------------------------------|----------------|-------------------------------------------------------------------------------------|
| BRD engine (SME questions, derive, maturity)       | **Real**       | `engines/brd_engine.py`; verified end-to-end by `iteration_1.json` (B-3, B-4).      |
| Architecture detection + gating + override         | **Real**       | `engines/architecture_engine.py`; blocked-combo logic returns `blocked=true`.        |
| Plan generation (file-by-file)                     | **Real**       | `engines/generation_engine.py::generate_plan`; 16+ files incl. all 13 mandatory.     |
| Frontend-only generation gating                    | **Partial**    | Architecture engine exists; **no enforced block** in `routes/generate.py` for the   |
|                                                    |                | "frontend-only requested but BRD needs backend" case beyond the architecture step.  |
| Full-stack generation                              | **Real**       | Confirmed: 2 prior workspaces contain real FE+BE scaffolds.                          |
| Build (real npm + pip)                             | **Real**       | `engines/build_engine.py`; PASS frontend, PARTIAL backend on iteration 1.            |
| Repair workflow (classify → patch → retry)         | **Real**       | `engines/repair_engine.py`; rollback-on-no-improvement is implemented.                |
| Snapshot/Rollback                                  | **Real**       | `engines/snapshot_engine.py`; pre-build snapshot via `state_machine`.                |
| Acceptance validation (honest)                     | **Real**       | `engines/acceptance_engine.py`; 15 checks, requirement coverage.                     |
| Export hygiene (ZIP + manifest + secret scan)      | **Real**       | `engines/export_engine.py`; 0 secrets in iteration 1.                                |
| **Improve/Fix workflow**                           | **MISSING**    | No `routes/improve.py`, no `engines/improve_engine.py`. **Phase 3 not started.**     |
| **Bounded AI customization**                       | **MISSING**    | No constraint registry / change budget logic exposed.                                |
| **Rework / Ingest existing project**               | **MISSING**    | No "upload my repo and continue from there" flow.                                    |
| **Resource discovery / import**                    | **MISSING**    | No internal asset/template/component library API.                                    |
| Honest 'unsupported feature' reporting in BRD      | **Real**       | BRD schema includes `requirements[].status: unsupported|blocked`.                     |
| Bounded changes during repair                      | **Real**       | Repair only writes files inside workspace; FORBIDDEN_PARTS guarded.                  |
| Secret hygiene in exports                          | **Real**       | Secret scan integrated; manifest exposes findings count.                              |

Net: **Phase 1 + Phase 2 are real**, Phase 3 (Improve/Fix + bounded customization),
Phase 4 (Repair-deepening + Rework), and Phase 5 (Resource discovery + polish) are
not yet started.

---

## 3. Critical Issues Found

### CRITICAL-1 — `requirements.txt` blocked clean install ✅ FIXED in this pass
- **Symptom:** `pip install -r backend/requirements.txt` failed with
  `Cannot install google-genai==2.0.1 and pydantic==2.7.1 because these package
  versions have conflicting dependencies`.
- **Impact:** Anyone redeploying or forking the repo could not bring the platform
  up. The currently-running venv works (pydantic 2.13.4 installed earlier), but
  `requirements.txt` did not reflect reality.
- **Root cause:** `google-genai 2.0.1` requires `pydantic>=2.9`, but
  requirements.txt pinned `pydantic==2.7.1` and `pydantic_core==2.18.2`.
- **Fix applied:** Replaced the three pins with
  `pydantic>=2.10,<3` + `pydantic-settings>=2.4,<3`, and removed the
  `pydantic_core` pin so pydantic resolves its own matching core.
- **Verification:** `pip install --dry-run -r requirements.txt` completes with
  `Exit code: 0` and resolves `pydantic-core 2.46.4` cleanly.

### CRITICAL-2 — Single-model LLM gateway (Flash for everything) ✅ FIXED in this pass
- **Symptom:** Every LLM call (plan generation, BRD derivation, repair patches,
  per-file code-gen) used `gemini-2.5-flash`. Plan + BRD derive + patch synthesis
  are the highest-value reasoning steps and were under-modelled.
- **Impact:** Lower-quality plans → more repair attempts → more total calls
  hitting the per-minute rate limit the user explicitly flagged.
- **Fix applied:** Added `tier` parameter to `LLMGateway.complete()`:
    - `tier="light"`  → `gemini-2.5-flash`  (default; per-file gen, BRD questions, classify)
    - `tier="heavy"`  → `gemini-2.5-pro`    (BRD derive, plan generation, repair patch)
  Heavy is invoked only once per pipeline phase, light absorbs the per-file
  volume. This is the *opposite* of "always Pro" — explicitly designed to reduce
  total calls while improving quality where it counts.
- **Verification:** `/api/system/health` now exposes:
  `tier_models: {"light":"gemini-2.5-flash","heavy":"gemini-2.5-pro"}`.

### HIGH-1 — Frontend-only gating is advisory, not enforced
- **Symptom:** If a user overrides architecture to `frontend_only` but the BRD
  requires a backend (e.g., notes app with persistence), the `routes/plan.py`
  endpoint refuses to proceed only when `decision.blocked == True`. If the
  override clears the block, the plan is generated and code is written.
- **Impact:** Violates BRD's "block invalid frontend-only generation paths"
  requirement. Generated app would look complete but secretly miss persistence.
- **Recommended fix (Phase 3 prereq):** In `architecture_engine.override`, never
  allow `frontend_only` when `requires_backend == True` from the deterministic
  classification (unless user explicitly acknowledges a 'demo-only' flag, which
  must propagate into Plan + Acceptance as `unsupported` requirements).

### HIGH-2 — Improve/Fix and Rework routes are entirely missing
- The BRD lists these as core capabilities. Once a project has been generated,
  there is no way to:
  - Request a bounded change (e.g., "add an /api/notes/search endpoint")
  - Ingest an existing repo and continue working on it
- **Recommended next phase** — see §4 below.

### MEDIUM-1 — Plan validation does not verify endpoint↔requirement mapping
- The plan asks the LLM to map each BRD requirement to a file or endpoint, but
  the platform doesn't *verify* that mapping post-generation. Acceptance engine
  checks requirement coverage by file name only.
- **Recommended fix:** in `acceptance_engine`, also check that every
  `endpoints[*].path` declared in the plan exists in `backend/main.py` source.

### MEDIUM-2 — Repair budget is fixed at 2 retries
- BRD calls for a configurable budget per project. Currently hard-coded.
- Trivial: surface as a project setting.

### LOW-1 — 6× react-hooks/exhaustive-deps warnings
- Not silently fixed (per user rule: "do not make less valuable fixes / keep
  making small fixes indefinitely"). Tracked here for a future polish pass.

### LOW-2 — `requirements.txt` is the output of a wide `pip freeze`
- Contains 130+ pins including `pandas`, `mypy`, `black`, `boto3`, `stripe`,
  `pillow`, etc. that the platform does not import. Slows installs and inflates
  Docker images. Cleanup is non-trivial (must distinguish real transitives from
  unused pins). Tracked for a dedicated dependency-audit pass.

### LOW-3 — `iteration_1.json` minor issue: build `overall_status` returns `null` in API
- Acknowledged in the prior test report. UI compensates. Not user-visible.

---

## 4. Proposed Next Execution Plan

Ordered by impact × tractability. **Phase 3 is the obvious next chunk**, and the
user should pick which slice to tackle first.

### Phase 3a — Improve/Fix workflow  (high impact, ~1 working session)
Goal: existing project + free-form change request → bounded patch applied, build,
re-run acceptance, optional new snapshot.

Deliverables:
- `engines/improve_engine.py` — given (workspace, plan, BRD, change_request),
  ask Pro for a JSON change manifest (list of file edits, max N files), apply,
  re-build, re-run acceptance, persist as `improve_attempt` in Mongo.
- `routes/improve.py` — `POST /api/projects/{id}/improve` (returns attempt id +
  diff summary); `GET /api/projects/{id}/improves`.
- Frontend `pages/Improve.jsx` — textarea + diff viewer + accept/reject toggle.
- Sidebar nav: insert between Build and Acceptance.

Safety: re-uses repair engine's safe-path guard + rollback-on-no-improvement.

### Phase 3b — Bounded AI customization registry
Goal: explicit constraint catalogue ("max 5 file edits", "no new top-level dirs",
"frontend changes only", etc.) attachable to every improve/repair call.

Deliverables: `engines/constraints.py` + `routes/projects.py` PUT support for
`project.constraints` + UI editor on Cockpit.

### Phase 4 — Rework / Ingest existing project
Goal: user uploads a ZIP or pastes a public repo URL; we run BRD-from-code,
architecture detect, then unlock Improve/Fix on it.

Deliverables: `routes/projects.py::ingest` (multipart + URL), `engines/ingest_engine.py`,
new dashboard CTA.

### Phase 5 — Resource discovery + polish
- Internal component library lookup (BRD knows what UI/data fragments exist).
- Polish: fix Low-1, Low-2; add per-project repair budget.

---

## 5. Highest-Impact Improvements Already Applied (this pass)

1. **`requirements.txt` install-blocker fixed** (CRITICAL-1).
2. **Hybrid Gemini tier routing** wired into the LLM gateway (CRITICAL-2):
   per-call `tier="heavy"` flag, applied at the 3 holistic-reasoning sites
   (BRD derive, plan generation, repair patch synthesis). Per-file generation
   intentionally stays on Flash to keep call volume cheap and stay under the
   per-minute rate limit.
3. **`/api/system/health` now exposes** `tier_models` + `default_tier` so the
   cockpit / smoke tests can verify wiring without LLM calls.

No working flow was removed, no architecture was silently replaced, no fallback
was weakened, and no LLM calls were made during this audit.

---

## 6. Open Decisions for the User

1. Which Phase 3 slice should we tackle first?
   a. **Phase 3a Improve/Fix end-to-end** (highest user value, ~1 session)
   b. Phase 3b Constraints registry first (prereq for safe 3a if you want hard
      bounds before exposing the surface)
   c. HIGH-1 Frontend-only gating tightening first (closes a BRD-compliance hole
      before adding new surface)
   d. Something else

2. Are there any *specific* generated-app quality complaints I should prioritize
   over green-field Phase 3 work? (e.g., "exports always have backend FAIL, fix
   the FastAPI stub" — let me know if so.)
