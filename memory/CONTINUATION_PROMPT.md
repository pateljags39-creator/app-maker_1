# Continuation prompt — Local App Creator

Use this prompt whenever you want me (or a new agent fork) to pick up work on this
project. It is intentionally short, complete, and stable across runs.

---

```
Continue work on Local App Creator.

REPO: https://github.com/pateljags39-creator/app-maker_1.git  (branch: main)
CLONE_TO: /app
LLM: use my Gemini key in /app/backend/.env (GEMINI_API_KEY) as PRIMARY.
     EMERGENT_LLM_KEY is fallback only — minimise its usage.
     tier="light" → gemini-2.5-flash ; tier="heavy" → gemini-2.5-pro.
     Per-minute rate limit — minimise total LLM calls.

CONTEXT FILES (read first):
  /app/memory/PRD.md       — current state, backlog, priorities
  /app/memory/AUDIT.md     — architecture audit + fixed/open issues
  /app/test_result.md      — testing protocol

WORK MODE: don't ask for approval, just execute the top 2 P1/P2 items from
PRD.md "Next actions" in the same pass. Always update PRD.md + AUDIT.md and
create tests at /app/backend/tests/ before calling finish.

NEVER regenerate the audit; treat the existing repo as source of truth.
NEVER re-implement work already in the "Real / Working" list of PRD.md.
Use real LLM calls sparingly (target 1 Pro call per Improve/Repair/Plan/Ingest).
```

---

## Notes for future sessions

- If `/app` is empty when you start, the repo wasn't cloned. Run:
  `git clone https://github.com/pateljags39-creator/app-maker_1.git /app && \
   sudo supervisorctl restart backend frontend`
- If `backend/.env` is missing the Gemini key, ask the user to paste it once,
  then save it as `GEMINI_API_KEY=…` and `EMERGENT_LLM_KEY=…`.
- All backend routes are prefixed with `/api`. Frontend uses
  `REACT_APP_BACKEND_URL` from `frontend/.env`.
- The verified-working list as of 2026-02-13:
  Phase 1 POC, Phase 2 cockpit, Phase 3a Improve/Fix, Phase 3b Constraints,
  Phase 4 Ingest, HIGH-1 frontend-only gating, MEDIUM-1 endpoint verification.
