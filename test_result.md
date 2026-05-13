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
  - task: "requirements.txt install-blocker fix"
    implemented: true
    working: "NA"
    file: "backend/requirements.txt"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Replaced pydantic==2.7.1 / pydantic_core==2.18.2 / pydantic-settings==2.2.1
          (conflicts with google-genai==2.0.1 which requires pydantic>=2.9) with
          pydantic>=2.10,<3 and pydantic-settings>=2.4,<3 and removed the
          pydantic_core pin. `pip install --dry-run -r requirements.txt` now
          resolves cleanly (verified). Runtime venv unaffected (already had
          pydantic 2.13.4). Backend health endpoint still returns 200 after restart.

  - task: "LLM gateway hybrid tier routing (Flash + 2.5 Pro)"
    implemented: true
    working: "NA"
    file: "backend/engines/llm_gateway.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Added per-call `tier` parameter to LLMGateway.complete():
            tier="light" -> gemini-2.5-flash  (default, used by per-file gen, BRD
                            questions, classify hints — high-volume, cheap)
            tier="heavy" -> gemini-2.5-pro    (BRD derive, plan generation,
                            repair patch synthesis — once per phase)
          Updated 3 callsites to pass tier="heavy":
            - engines/brd_engine.py::derive_brd
            - engines/generation_engine.py::generate_plan
            - engines/repair_engine.py::_ask_patch
          `/api/system/health` now exposes `tier_models` and `default_tier` for
          observability. Lint passes. Module imports OK in venv.

  - task: "Audit report committed"
    implemented: true
    working: "NA"
    file: "memory/AUDIT.md"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Wrote comprehensive audit at /app/memory/AUDIT.md: architecture audit,
          module map, implementation status matrix mapped to BRD phases,
          critical/high/medium/low findings, and proposed Phase 3+ execution plan.
          No code paths were silently rewritten; only the 2 fixes above were applied.

frontend: []

metadata:
  created_by: "main_agent"
  version: "0.2.1"
  test_sequence: 1
  run_ui: false

test_plan:
  current_focus:
    - "requirements.txt install-blocker fix"
    - "LLM gateway hybrid tier routing (Flash + 2.5 Pro)"
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
      Waiting for user decision on which Phase 3 slice to tackle next (Improve/Fix
      vs constraints registry vs frontend-only gating tightening).