"""Generation engine: LLM-driven, file-by-file full-stack scaffold generator.

Generated stack default: React + Vite (frontend) + FastAPI (Python) + SQLite (backend).
The LLM is asked for a structured plan and then for each file's content. Honest.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .llm_gateway import LLMGateway, LLMError

logger = logging.getLogger("engines.generation_engine")

PLAN_SYSTEM = """You are the planning component of an AI software-factory.
Given a structured BRD and an architecture decision, you produce a STRICT JSON plan that lists every file the generator must produce.

The target stack is FIXED:
  - frontend: React 18 + Vite 5 (JavaScript, no TypeScript). Tailwind optional but allowed.
  - backend: FastAPI (Python 3.11), SQLAlchemy 2 with SQLite, Pydantic v2.
  - runtime expectation: `npm install && npm run build` produces frontend/dist; `pip install -r requirements.txt && python -c 'import main'` succeeds on backend.

Return ONLY JSON of shape:
{
  "app_name": "<kebab-case-name>",
  "summary": "<one-paragraph overview of what is being built>",
  "files": [...],
  "endpoints": [{"method": "GET", "path": "/api/notes", "purpose": "list notes"}],
  "entities": [{"name": "Note", "fields": [{"name":"id","type":"int"}]}]
}

MANDATORY files in `files` (in this order):
  1. backend/requirements.txt
  2. backend/database.py
  3. backend/models.py
  4. backend/schemas.py
  5. backend/main.py
  6. frontend/package.json
  7. frontend/vite.config.js
  8. frontend/index.html
  9. frontend/src/main.jsx
 10. frontend/src/styles.css
 11. frontend/src/api.js
 12. frontend/src/App.jsx
 13. README.md

You MAY add up to 5 additional files (small focused components/pages) but no more.

Rules:
- Every BRD requirement must map to >= 1 endpoint or file.
- Do NOT add auth/payments/3p integrations unless BRD explicitly asks for them.
- Keep the file list minimal but complete; only files you will actually write.
- App.jsx must work with WHATEVER pages/components you include. If you don't include extras, App.jsx must be self-contained.
"""

FILE_SYSTEM = """You are the code-writing component of an AI software-factory.
Write the COMPLETE content for ONE file inside the agreed plan. No partial files. No placeholders or TODOs unless absolutely necessary; if a placeholder is needed it must be clearly labelled as such.

Return ONLY the raw file contents. No JSON envelope. No prose. No commentary.
If your runtime forces some marker, you MAY wrap in a single fenced code block like ```<lang>\\n<file content>\\n```, but no other text. The system will strip the fences automatically.

Hard rules:
- Match the agreed stack exactly: React 18 + Vite 5, JavaScript, FastAPI, SQLAlchemy 2 + SQLite, Pydantic v2.
- frontend/package.json must include: react, react-dom (^18), vite (^5), @vitejs/plugin-react, and scripts: dev, build, preview.
- frontend/vite.config.js: import @vitejs/plugin-react; defaults are fine.
- frontend/src/main.jsx: ReactDOM.createRoot mount on #root; import App; import './styles.css'.
- frontend/index.html: <div id="root"></div>, <script type="module" src="/src/main.jsx"></script>.
- frontend api base URL must come from import.meta.env.VITE_API_URL with fallback http://localhost:8000.

BACKEND IMPORT RULES (CRITICAL):
- Use ABSOLUTE imports only inside backend/ files. Example: `from database import ...`, `from models import ...`. NEVER use `from .database import ...` or `from .models import ...`. The backend is run as a flat package via `python -c "import main"`.
- Only `database.py` declares `Base = declarative_base()`. Every other backend file imports Base from database.py (e.g., `from database import Base`). NEVER redeclare `Base` in models.py / schemas.py / main.py.
- main.py must:
  * `app = FastAPI(); CORS middleware allow_origins=['*']`
  * use `APIRouter(prefix='/api')` and `app.include_router(...)`
  * call `Base.metadata.create_all(bind=engine)` at module level (after imports) OR at startup event
  * include `if __name__ == "__main__": uvicorn.run("main:app", ...)`.
- backend/database.py: SQLAlchemy 2 engine with `sqlite:///./app.db`, SessionLocal, Base (the ONE Base).
- backend/models.py: SQLAlchemy models for declared entities with __tablename__; `from database import Base` only — do NOT call declarative_base again.
- backend/schemas.py: Pydantic v2 schemas (ConfigDict(from_attributes=True)).
- backend/requirements.txt: pin reasonable versions; include fastapi, uvicorn[standard], sqlalchemy>=2, pydantic>=2, python-multipart.
- README.md must include: prerequisites, frontend run, backend run, ports, env.

NO secrets in any file. NEVER reference Gemini/Emergent keys.
"""


@dataclass
class GenerationResult:
    plan: dict[str, Any]
    files_written: list[str] = field(default_factory=list)
    provider_log: list[str] = field(default_factory=list)
    workspace: str = ""


async def generate_plan(
    gateway: LLMGateway,
    brd: dict[str, Any],
    architecture: dict[str, Any],
) -> dict[str, Any]:
    user = (
        "# BRD\n```json\n" + json.dumps(brd, indent=2) + "\n```\n\n"
        "# Architecture decision\n```json\n" + json.dumps(architecture, indent=2) + "\n```\n\n"
        "Produce the JSON plan as specified."
    )
    resp = await gateway.complete(
        system=PLAN_SYSTEM,
        user=user,
        json_mode=True,
        temperature=0.1,
        max_output_tokens=6000,
    )
    plan = resp.as_json()
    if not isinstance(plan, dict) or "files" not in plan:
        raise LLMError(f"invalid plan shape: {type(plan).__name__}")
    return plan


def _validate_path(rel: str) -> bool:
    if not rel or rel.startswith("/") or ".." in Path(rel).parts:
        return False
    parts = set(Path(rel).parts)
    if parts & {".env", ".factory", "node_modules", ".git", "__pycache__", "dist", "build"}:
        return False
    return True


async def generate_file(
    gateway: LLMGateway,
    plan: dict[str, Any],
    file_entry: dict[str, Any],
    brd: dict[str, Any] | None = None,
) -> str:
    """Ask LLM for a single file's full content. Returns string content.

    Uses PLAINTEXT mode (not JSON-wrapped) for efficiency and reliability.
    Strips code fences if present. Retries once on empty/garbage output.
    """
    user_blocks = [
        f"# Target file: {file_entry['path']}",
        f"# Purpose: {file_entry.get('purpose','')}",
        f"# Kind: {file_entry.get('kind','code')}",
        "# Full plan (for context):",
        "```json\n" + json.dumps(plan, indent=2)[:8000] + "\n```",
    ]
    if brd is not None:
        user_blocks.append("# BRD (for context):\n```json\n" + json.dumps(brd, indent=2)[:4000] + "\n```")
    user_blocks.append(
        f"Write the complete contents of `{file_entry['path']}` now. "
        "Return ONLY the file content. No JSON, no prose, no explanation."
    )
    user = "\n\n".join(user_blocks)

    last_err: Exception | None = None
    for attempt in range(2):
        try:
            resp = await gateway.complete(
                system=FILE_SYSTEM,
                user=user,
                json_mode=False,
                temperature=0.1,
                max_output_tokens=12000,
            )
            content = _strip_fences(resp.text)
            if not content or not content.strip():
                raise LLMError(f"empty content for {file_entry['path']}")
            return content
        except (LLMError, Exception) as e:
            last_err = e
            logger.warning("generate_file attempt %d failed for %s: %s", attempt + 1, file_entry["path"], e)
            continue
    raise LLMError(f"failed to generate {file_entry['path']}: {last_err}")


def _strip_fences(text: str) -> str:
    """Strip a single leading/trailing ``` fence if present."""
    import re as _re
    s = text.strip()
    # remove leading ```<lang>\n
    m = _re.match(r"^```[a-zA-Z0-9_+\-.]*\s*\n", s)
    if m:
        s = s[m.end():]
        # remove trailing ```
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3].rstrip("\n")
    # If the entire thing is wrapped: ```...```
    m2 = _re.match(r"^```(?:[a-zA-Z0-9_+\-.]*)?\s*(.*?)\s*```$", s, _re.DOTALL)
    if m2:
        s = m2.group(1)
    return s


async def generate_project(
    gateway: LLMGateway,
    brd: dict[str, Any],
    architecture: dict[str, Any],
    workspace: Path,
) -> GenerationResult:
    workspace = Path(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    plan = await generate_plan(gateway, brd, architecture)
    res = GenerationResult(plan=plan, workspace=str(workspace))

    failed: list[dict[str, Any]] = []
    for entry in plan.get("files", []):
        # Normalize entry: accept string paths or dicts.
        if isinstance(entry, str):
            entry = {"path": entry, "purpose": "", "kind": "code"}
        elif not isinstance(entry, dict):
            logger.warning("Skipping non-string/dict entry in plan.files: %r", entry)
            continue
        rel = entry.get("path", "")
        if not _validate_path(rel):
            logger.warning("Skipping unsafe/invalid path: %s", rel)
            continue
        try:
            content = await generate_file(gateway, plan, entry, brd=brd)
        except LLMError as e:
            logger.warning("LLM failed for %s: %s", rel, e)
            failed.append(entry)
            continue
        out = workspace / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        res.files_written.append(rel)

    # Retry critical missing files once more (only critical ones).
    critical = {
        "backend/main.py", "backend/requirements.txt", "backend/database.py", "backend/models.py", "backend/schemas.py",
        "frontend/package.json", "frontend/index.html", "frontend/vite.config.js",
        "frontend/src/main.jsx", "frontend/src/App.jsx",
    }
    for entry in list(failed):
        rel = entry.get("path", "")
        if rel in critical:
            try:
                content = await generate_file(gateway, plan, entry, brd=brd)
                out = workspace / rel
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(content, encoding="utf-8")
                res.files_written.append(rel)
                failed.remove(entry)
                logger.info("Recovered critical file on second pass: %s", rel)
            except LLMError as e:
                logger.error("Critical file STILL failing after retry: %s -- %s", rel, e)

    # Synthesize bare-minimum critical files if STILL missing, so build can start.
    if architecture.get("requires_backend"):
        for rel, factory in [
            ("backend/main.py", _stub_backend_main),
            ("backend/database.py", _stub_database),
            ("backend/requirements.txt", _stub_requirements),
        ]:
            if not (workspace / rel).exists():
                content = factory(plan)
                (workspace / rel).parent.mkdir(parents=True, exist_ok=True)
                (workspace / rel).write_text(content, encoding="utf-8")
                res.files_written.append(rel)
                logger.warning("Synthesized stub for missing critical file: %s", rel)

    if architecture.get("kind") != "backend_required":
        for rel, factory in [
            ("frontend/package.json", _stub_package_json),
            ("frontend/vite.config.js", _stub_vite_config),
            ("frontend/index.html", _stub_index_html),
            ("frontend/src/main.jsx", _stub_main_jsx),
            ("frontend/src/styles.css", _stub_styles),
        ]:
            if not (workspace / rel).exists():
                content = factory(plan)
                (workspace / rel).parent.mkdir(parents=True, exist_ok=True)
                (workspace / rel).write_text(content, encoding="utf-8")
                res.files_written.append(rel)
                logger.warning("Synthesized stub for missing critical file: %s", rel)

    # Deterministic post-processing fix-ups for the most common LLM mistakes.
    _post_fixups(workspace)
    _ensure_frontend_deps(workspace)
    _ensure_backend_deps(workspace)

    # Also drop a minimal package-lock-free .gitignore for honesty in exports.
    (workspace / ".gitignore").write_text(
        "node_modules\n.venv\n__pycache__\n*.pyc\n.env\n.env.local\n.factory\ndist\nbuild\n",
        encoding="utf-8",
    )
    res.files_written.append(".gitignore")
    return res


def _post_fixups(workspace: Path) -> None:
    """Apply rule-based fixes that don't need the LLM:
    - convert backend relative imports `from .foo` -> `from foo`
    - remove duplicated `Base = declarative_base()` in non-database files
    - make sure database.py defines Base (LLM occasionally omits it)
    """
    import re as _re
    backend = workspace / "backend"
    if not backend.exists():
        return
    rel_imp_rx = _re.compile(r"(^|\n)from\s+\.([\w\.]+)\s+import", _re.MULTILINE)
    rel_imp2_rx = _re.compile(r"(^|\n)import\s+\.([\w\.]+)", _re.MULTILINE)
    db_decl_rx = _re.compile(r"(^|\n)Base\s*=\s*declarative_base\(\)\s*", _re.MULTILINE)
    for p in backend.rglob("*.py"):
        try:
            text = p.read_text("utf-8", "replace")
        except Exception:
            continue
        original = text
        # Replace `from .x import` with `from x import`
        text = rel_imp_rx.sub(lambda m: f"{m.group(1)}from {m.group(2)} import", text)
        text = rel_imp2_rx.sub(lambda m: f"{m.group(1)}import {m.group(2)}", text)
        # If this file is NOT database.py, and it declares Base = declarative_base(), drop it and use shared one.
        if p.name != "database.py" and db_decl_rx.search(text):
            text = db_decl_rx.sub("\n", text)
            if "from database import" not in text and "Base" in text:
                # Ensure Base is imported from database
                text = "from database import Base\n" + text
        if text != original:
            p.write_text(text, encoding="utf-8")
    # Ensure database.py exists and exports Base.
    dbp = backend / "database.py"
    if dbp.exists():
        try:
            db_text = dbp.read_text("utf-8", "replace")
            if "Base" not in db_text:
                db_text += "\nfrom sqlalchemy.orm import declarative_base\nBase = declarative_base()\n"
                dbp.write_text(db_text, encoding="utf-8")
        except Exception:
            pass


# ---------- Dependency scanners ----------
# Well-known npm package name versions used when LLM imports without declaring.
_NPM_FALLBACK_VERSIONS = {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.0",
    "react-router": "^6.22.0",
    "axios": "^1.6.0",
    "zustand": "^4.5.0",
    "swr": "^2.2.0",
    "@tanstack/react-query": "^5.0.0",
    "clsx": "^2.0.0",
    "classnames": "^2.5.0",
    "date-fns": "^3.0.0",
    "dayjs": "^1.11.10",
    "lucide-react": "^0.350.0",
    "react-icons": "^5.0.0",
    "framer-motion": "^11.0.0",
    "recharts": "^2.12.0",
    "uuid": "^9.0.0",
    "react-hot-toast": "^2.4.0",
    "sonner": "^1.4.0",
    "react-helmet": "^6.1.0",
}
_STDLIB_PY = {
    "os", "sys", "json", "re", "time", "datetime", "math", "uuid", "pathlib", "typing", "io",
    "collections", "itertools", "functools", "logging", "asyncio", "subprocess", "tempfile",
    "shutil", "hashlib", "base64", "string", "enum", "dataclasses", "contextlib", "random",
    "secrets", "abc", "warnings", "traceback", "csv", "html", "urllib", "concurrent", "queue",
    "threading", "operator", "copy", "weakref", "heapq", "decimal", "fractions",
}
_PIP_KNOWN = {
    "fastapi", "uvicorn", "sqlalchemy", "pydantic", "python-multipart", "aiosqlite",
    "alembic", "passlib", "bcrypt", "python-jose", "pyjwt", "httpx", "requests", "starlette",
    "python-dotenv", "redis", "celery", "boto3", "pillow",
}


def _ensure_frontend_deps(workspace: Path) -> None:
    import re as _re
    import json as _json
    fe = workspace / "frontend"
    pj = fe / "package.json"
    if not pj.exists():
        return
    try:
        pkg = _json.loads(pj.read_text(encoding="utf-8"))
    except Exception:
        return
    deps = dict(pkg.get("dependencies") or {})
    dev = dict(pkg.get("devDependencies") or {})

    # Collect bare imports from .js/.jsx files.
    found: set[str] = set()
    imp_rx = _re.compile(r"""(?:import\s+[^'"]*?from\s+['"]([^'"]+)['"])|(?:require\(\s*['"]([^'"]+)['"]\s*\))""")
    for p in fe.rglob("*.js*"):
        if "node_modules" in p.parts:
            continue
        try:
            text = p.read_text("utf-8", "replace")
        except Exception:
            continue
        for m in imp_rx.finditer(text):
            spec = m.group(1) or m.group(2)
            if not spec or spec.startswith((".", "/", "@/")):
                continue
            # extract package name (scoped @ns/pkg or simple)
            if spec.startswith("@"):
                parts = spec.split("/")
                pkgname = "/".join(parts[:2])
            else:
                pkgname = spec.split("/")[0]
            if pkgname:
                found.add(pkgname)

    # Add any missing ones using fallback versions.
    changed = False
    for pkgname in sorted(found):
        if pkgname in deps or pkgname in dev:
            continue
        ver = _NPM_FALLBACK_VERSIONS.get(pkgname)
        if ver is None:
            # skip unknown to avoid breaking installs
            continue
        deps[pkgname] = ver
        changed = True

    # Ensure absolute essentials
    for k, v in [("react", "^18.2.0"), ("react-dom", "^18.2.0")]:
        if k not in deps and k not in dev:
            deps[k] = v
            changed = True
    for k, v in [("@vitejs/plugin-react", "^4.2.0"), ("vite", "^5.0.0")]:
        if k not in deps and k not in dev:
            dev[k] = v
            changed = True

    if changed:
        pkg["dependencies"] = deps
        pkg["devDependencies"] = dev
        pj.write_text(_json.dumps(pkg, indent=2) + "\n", encoding="utf-8")


def _ensure_backend_deps(workspace: Path) -> None:
    import re as _re
    be = workspace / "backend"
    req = be / "requirements.txt"
    if not req.exists():
        return
    text = req.read_text(encoding="utf-8")
    have_lower = {line.split("==")[0].split(">=")[0].split("<=")[0].lower().strip(): line for line in text.splitlines() if line.strip() and not line.strip().startswith("#")}

    imp_rx = _re.compile(r"^\s*(?:from|import)\s+([\w_.]+)", _re.MULTILINE)
    found: set[str] = set()
    for p in be.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        try:
            t = p.read_text("utf-8", "replace")
        except Exception:
            continue
        for m in imp_rx.finditer(t):
            top = m.group(1).split(".")[0]
            if top in _STDLIB_PY:
                continue
            if top in {"engines", "api", "models", "schemas", "database", "main", "config", "utils", "tests"}:
                continue
            found.add(top.lower())

    # Map well-known module names to pypi packages
    module_to_pkg = {
        "fastapi": "fastapi==0.110.1",
        "uvicorn": "uvicorn[standard]==0.25.0",
        "sqlalchemy": "sqlalchemy>=2.0.0",
        "pydantic": "pydantic>=2.6.0",
        "multipart": "python-multipart>=0.0.9",
        "dotenv": "python-dotenv>=1.0.0",
        "passlib": "passlib>=1.7.4",
        "bcrypt": "bcrypt==4.1.3",
        "jose": "python-jose>=3.3.0",
        "jwt": "pyjwt>=2.10.1",
        "httpx": "httpx>=0.27.0",
        "requests": "requests>=2.31.0",
        "redis": "redis>=5.0.0",
        "boto3": "boto3>=1.34.0",
        "PIL": "pillow>=10.0.0",
        "pil": "pillow>=10.0.0",
        "pillow": "pillow>=10.0.0",
        "starlette": "starlette>=0.36.0",
        "aiosqlite": "aiosqlite>=0.19.0",
    }

    added = []
    for top in sorted(found):
        pkg_line = module_to_pkg.get(top)
        if not pkg_line:
            continue
        pkg_name = pkg_line.split("==")[0].split(">=")[0].split("[")[0].lower()
        if pkg_name in have_lower:
            continue
        added.append(pkg_line)
        have_lower[pkg_name] = pkg_line

    if added:
        new_text = text.rstrip("\n") + "\n" + "\n".join(added) + "\n"
        req.write_text(new_text, encoding="utf-8")


# ---------- emergency stubs (clearly labelled) ----------
def _stub_backend_main(plan: dict[str, Any]) -> str:
    return '''"""Auto-synthesized fallback main.py. Replace with proper implementation."""
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

try:
    from database import Base, engine  # noqa: F401
    Base.metadata.create_all(bind=engine)
except Exception:
    pass

app = FastAPI(title="Generated App (fallback main)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

api = APIRouter(prefix="/api")

@api.get("/health")
def health() -> dict:
    return {"status": "ok", "note": "fallback main.py - synthesize-on-missing"}

app.include_router(api)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
'''


def _stub_database(plan: dict[str, Any]) -> str:
    return '''"""SQLAlchemy 2 + SQLite (fallback)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
'''


def _stub_requirements(plan: dict[str, Any]) -> str:
    return "fastapi==0.110.1\nuvicorn[standard]==0.25.0\nsqlalchemy>=2.0.0\npydantic>=2.6.0\npython-multipart>=0.0.9\n"


def _stub_package_json(plan: dict[str, Any]) -> str:
    name = (plan.get("app_name") or "generated-app").lower().replace(" ", "-")
    return json.dumps({
        "name": name,
        "private": True,
        "version": "0.1.0",
        "type": "module",
        "scripts": {"dev": "vite", "build": "vite build", "preview": "vite preview"},
        "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"},
        "devDependencies": {"@vitejs/plugin-react": "^4.2.0", "vite": "^5.0.0"},
    }, indent=2) + "\n"


def _stub_vite_config(plan: dict[str, Any]) -> str:
    return '''import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
});
'''


def _stub_index_html(plan: dict[str, Any]) -> str:
    name = plan.get("app_name") or "App"
    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{name}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
'''


def _stub_main_jsx(plan: dict[str, Any]) -> str:
    return '''import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './styles.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
'''


def _stub_styles(plan: dict[str, Any]) -> str:
    return "body { margin: 0; font-family: system-ui, sans-serif; }\n"
