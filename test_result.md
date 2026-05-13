#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: |
  Continue building Local App Creator — a local-first AI software-engineering platform
  (BRD-driven app creation, architecture detection/gating, frontend + full-stack
  generation, improve/fix, bounded customization, repair, rework, acceptance,
  exports, snapshots/rollback). Repo `pateljags39-creator/app-maker_1` @ main was
  pulled into /app. User requested: audit + immediately apply top 1–2 highest-impact
  fixes in same pass. LLM backbone: Google Gemini (Flash for small/light calls,
  2.5 Pro for major tasks). Minimise LLM calls — per-minute rate limit.

backend:
  - task: "Phase 3b — Bounded-customization constraints registry"
    implemented: true
    working: "NA"
    file: "backend/engines/constraints.py, backend/routes/constraints.py, backend/repositories.py, backend/engines/repair_engine.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Added ProjectConstraints dataclass + validate_change() with hard rules
          (forbidden paths, secret regex, workspace escape detection) and tunable
          budgets (max_files_changed=8, max_new_files=5, max_total_loc_changed=1500,
          allowed_areas, no_new_top_level_dirs, dep change toggles).
          - GET/PUT/POST-reset endpoints under /api/projects/{id}/constraints
          - Mongo collection `constraints` with unique index on project_id
          - WIRED into repair_engine.attempt_repairs(...) and through both
            routes/build.py and routes/generate.py — repair patches now go
            through validate_change() before any file is written; violations
            are recorded in the RepairAttempt note and the patch is skipped.
          Smoke-tested live: GET returns defaults, PUT persists custom values,
          area filter strips invalid entries, POST reset works.

  - task: "Phase 3a — Improve/Fix workflow end-to-end"
    implemented: true
    working: "NA"
    file: "backend/engines/improve_engine.py, backend/routes/improve.py, backend/repositories.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          New ImproveAttempt pipeline:
            1. create_snapshot() pre-change for rollback
            2. ask gemini-2.5-pro (tier="heavy") for JSON manifest with WHOLE
               file contents per change (no diff/patch format)
            3. validate manifest against constraints (deterministic)
            4. apply atomically with safe-path checks
            5. real npm + pip rebuild via build_engine.run_build()
            6. AUTO-ROLLBACK on build regression (compares to last_build_status)
            7. re-run acceptance for honest read-out
          Possible statuses: applied | rolled_back | rejected_by_constraints |
          llm_failed | pending. Each persisted to new improve_attempts collection
          with full file deltas (before/after sha256 + line counts).
          Routes: POST /api/projects/{id}/improve, GET list, GET single attempt.
          Ledger events: improve.requested, improve.applied, improve.rolled_back,
          improve.rejected_by_constraints, improve.llm_failed.
          Designed for minimal LLM calls: exactly 1 Pro call per request, no
          per-file chatter. NOT yet end-to-end tested with a real LLM call
          (per user "minimise LLM calls" constraint — schedule a real run
          when a fully-generated project is available).

frontend:
  - task: "Improve / Fix page + Constraints page + nav entries"
    implemented: true
    working: "NA"
    file: "frontend/src/pages/Improve.jsx, frontend/src/pages/Constraints.jsx, frontend/src/App.js, frontend/src/components/cockpit/AppShell.jsx, frontend/src/lib/api.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Two new cockpit pages wired into routing and sidebar:
          - /projects/{id}/constraints — full editor (change budget, scope,
            dependencies, notes) with Save / Reset to defaults. Hard rules
            displayed as always-on info card.
          - /projects/{id}/improve — change-request textarea + constraint
            pills + past-attempts list with status badges, expandable diff
            summary (file actions, LOC deltas, violations, npm/pip deps,
            unsupported items, error messages, snapshot id on rollback).
          New API client methods: getConstraints / putConstraints /
          resetConstraints / requestImprove / listImproves / getImprove.
          Lint passes; UI smoke tested via screenshot — Constraints page
          renders fully (all form fields visible), sidebar shows both new
          entries with proper Lucide icons (Wand2 for Improve, Shield for
          Constraints) between Acceptance and Export.

metadata:
  created_by: "main_agent"
  version: "0.3.0"
  test_sequence: 2
  run_ui: false

test_plan:
  current_focus:
    - "Phase 3b — Bounded-customization constraints registry"
    - "Phase 3a — Improve/Fix workflow end-to-end"
    - "Improve / Fix page + Constraints page + nav entries"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
  - agent: "main"
    message: |
      Continuation pass complete. Cloned repo into /app, recreated .env files
      (Gemini key + Emergent fallback key wired), brought platform up. Backend
      health green: primary_available=true, fallback_available=true, tier_models
      now reported. Applied 2 highest-impact fixes (CRITICAL-1 requirements.txt
      install conflict; CRITICAL-2 hybrid model routing). Audit at memory/AUDIT.md.
  - agent: "main"
    message: |
      Phase 3a + 3b shipped in same pass per user request "do a and b".
      Backend: constraints engine + improve engine + 4 new routes wired into
      Mongo + repair engine now respects per-project constraints.
      Frontend: 2 new pages, sidebar nav, api.js extensions.
      Verified via direct API calls (constraints CRUD) and screenshots
      (Constraints page fully renders, Improve page testid materialized).
      Improve full LLM round-trip not yet exercised to honour the user's
      per-minute Gemini rate limit; safe to run from the UI when desired.