"""Ingest engine: import an existing project from a ZIP upload or git URL.

Responsibilities:
  1. SAFELY extract a ZIP or shallow-clone a public HTTPS git URL into a workspace.
  2. Strip dangerous / heavy paths (.git, node_modules, dist, etc.).
  3. Detect tech stack deterministically from package.json + requirements.txt.
  4. Detect architecture deterministically from the detected stack.
  5. Synthesize a plan (file index + endpoint list) from the existing tree (no LLM).
  6. Derive a BRD-FROM-CODE via a SINGLE Pro-tier LLM call (heavy reasoning).

Safety rules (non-negotiable, enforced inline):
  * ZIP entries must NOT escape the workspace (zip-slip guard).
  * Total uncompressed size capped to MAX_UNCOMPRESSED.
  * File count capped to MAX_FILES.
  * Symlinks in ZIPs are dropped.
  * Git URLs must be http(s)://; localhost/private IPs are refused.
  * Per-file size and per-path length capped.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import shutil
import subprocess
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .llm_gateway import LLMError, LLMGateway

logger = logging.getLogger("engines.ingest_engine")

# ---------- Safety limits ----------
MAX_ZIP_BYTES = 100 * 1024 * 1024        # 100 MB compressed input
MAX_UNCOMPRESSED = 300 * 1024 * 1024     # 300 MB on-disk after extract
MAX_FILES = 5_000                        # entries in zip
MAX_PATH_LEN = 260                       # per-entry path length
MAX_PER_FILE_BYTES = 20 * 1024 * 1024    # 20 MB single file ceiling
STRIP_DIRS: set[str] = {
    "node_modules", "__pycache__", ".git", "dist", "build",
    ".venv", ".next", "vendor", ".turbo", ".cache", ".pytest_cache",
    ".mypy_cache", ".idea", ".vscode",
}
ALLOWED_GIT_SCHEMES = ("http://", "https://")
GIT_CLONE_TIMEOUT_SEC = 90


# ---------- Public types ----------
@dataclass
class IngestSummary:
    files_imported: int = 0
    bytes_imported: int = 0
    warnings: list[str] = field(default_factory=list)


# ---------- ZIP extraction ----------
def safe_extract_zip(src: Path, dest: Path) -> IngestSummary:
    """Extract `src` zip into `dest` safely; returns IngestSummary."""
    summary = IngestSummary()
    dest.mkdir(parents=True, exist_ok=True)
    dest_resolved = dest.resolve()

    if not zipfile.is_zipfile(src):
        raise ValueError("not_a_zip_file")

    with zipfile.ZipFile(src) as zf:
        members = zf.infolist()
        if len(members) > MAX_FILES:
            raise ValueError(f"zip has {len(members)} entries (max {MAX_FILES})")

        for m in members:
            if m.is_dir():
                continue
            name = m.filename.replace("\\", "/")
            # Reject absolute paths and parent escapes.
            if name.startswith("/") or ".." in Path(name).parts:
                summary.warnings.append(f"skipped suspicious path: {name}")
                continue
            # Skip stripped dirs entirely.
            if any(part in STRIP_DIRS for part in Path(name).parts):
                continue
            if len(name) > MAX_PATH_LEN:
                summary.warnings.append(f"skipped long path: {name[:60]}…")
                continue
            if m.file_size > MAX_PER_FILE_BYTES:
                summary.warnings.append(
                    f"skipped huge file: {name} ({m.file_size // 1024} KB)"
                )
                continue
            if summary.bytes_imported + m.file_size > MAX_UNCOMPRESSED:
                summary.warnings.append(
                    f"hit total uncompressed budget at {name}; stopped"
                )
                break
            # Reject symlinks (in zip external_attr high nibble == 0xA).
            if (m.external_attr >> 28) == 0xA:
                summary.warnings.append(f"skipped symlink: {name}")
                continue

            target = (dest / name).resolve()
            try:
                target.relative_to(dest_resolved)
            except ValueError:
                summary.warnings.append(f"skipped zip-slip path: {name}")
                continue

            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(m) as src_f, target.open("wb") as dst_f:
                shutil.copyfileobj(src_f, dst_f, length=1024 * 256)
            summary.files_imported += 1
            summary.bytes_imported += m.file_size

    # If the ZIP wrapped everything under a single top-level dir (very common
    # for github exports like 'repo-main/...'), hoist it up so the workspace
    # has the expected structure.
    _maybe_flatten_top(dest)
    return summary


def _maybe_flatten_top(dest: Path) -> None:
    """If `dest` has exactly one child dir and no files, move children up."""
    try:
        kids = [p for p in dest.iterdir() if p.name not in STRIP_DIRS]
    except FileNotFoundError:
        return
    if len(kids) != 1 or not kids[0].is_dir():
        return
    top = kids[0]
    for child in list(top.iterdir()):
        shutil.move(str(child), str(dest / child.name))
    try:
        top.rmdir()
    except OSError:
        pass


# ---------- Git clone ----------
def validate_git_url(url: str) -> str:
    u = (url or "").strip()
    if not u:
        raise ValueError("git_url_empty")
    if not any(u.startswith(s) for s in ALLOWED_GIT_SCHEMES):
        raise ValueError("unsupported git URL scheme: only http(s):// allowed")
    low = u.lower()
    for bad in ("localhost", "127.0.0.1", "0.0.0.0", "://192.168.", "://10.",
                "://172.16.", "://172.17.", "://172.18.", "://172.19.",
                "://172.20.", "://172.21.", "://172.22.", "://172.23.",
                "://172.24.", "://172.25.", "://172.26.", "://172.27.",
                "://172.28.", "://172.29.", "://172.30.", "://172.31."):
        if bad in low:
            raise ValueError("private/local URLs are not accepted")
    return u


def clone_git_url(url: str, dest: Path) -> IngestSummary:
    """Shallow-clone `url` into `dest`, then strip heavy dirs. Sync (use in worker)."""
    summary = IngestSummary()
    safe_url = validate_git_url(url)
    dest.mkdir(parents=True, exist_ok=True)
    # If dest non-empty git will refuse; clean it first.
    if any(dest.iterdir()):
        for p in list(dest.iterdir()):
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                try:
                    p.unlink()
                except FileNotFoundError:
                    pass
    cmd = [
        "git", "clone", "--depth=1", "--single-branch",
        "--config", "core.longpaths=true",
        safe_url, str(dest),
    ]
    env = {"GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "echo", "PATH": "/usr/bin:/bin"}
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=GIT_CLONE_TIMEOUT_SEC, env=env,
        )
    except subprocess.TimeoutExpired:
        raise ValueError(f"git clone timed out after {GIT_CLONE_TIMEOUT_SEC}s") from None
    if result.returncode != 0:
        # Truncate stderr to avoid leaking long credentials.
        err = (result.stderr or "").strip().splitlines()[-1:][:1]
        raise ValueError(f"git_clone_failed: {' '.join(err)[:240]}")

    # Strip .git and heavy dirs.
    for d in STRIP_DIRS:
        for p in dest.rglob(d):
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)

    # Count.
    files = 0
    bytes_total = 0
    for p in dest.rglob("*"):
        if not p.is_file():
            continue
        try:
            bytes_total += p.stat().st_size
        except FileNotFoundError:
            continue
        files += 1
        if bytes_total > MAX_UNCOMPRESSED:
            summary.warnings.append(
                f"clone exceeded {MAX_UNCOMPRESSED // 1024 // 1024} MB; trimming further may be needed"
            )
            break
    summary.files_imported = files
    summary.bytes_imported = bytes_total
    return summary


# ---------- Stack + architecture detection ----------
def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text("utf-8"))
    except Exception:
        return {}


def detect_stack(workspace: Path) -> dict[str, Any]:
    """Deterministic detection of the project shape."""
    stack: dict[str, Any] = {
        "has_frontend": False, "has_backend": False, "has_db": False,
        "frontend_framework": "", "backend_framework": "",
        "db_engine": "",
        "languages": [],
        "structure": "flat",
    }
    fe = workspace / "frontend"
    be = workspace / "backend"
    if fe.exists() and be.exists():
        stack["structure"] = "monorepo"

    # Frontend
    for pp in (fe / "package.json", workspace / "package.json"):
        if pp.exists():
            pkg = _read_json(pp)
            deps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {})}
            stack["has_frontend"] = True
            if "next" in deps:
                stack["frontend_framework"] = "nextjs"
            elif "vite" in deps:
                stack["frontend_framework"] = "vite"
            elif "react-scripts" in deps:
                stack["frontend_framework"] = "cra"
            elif "@angular/core" in deps:
                stack["frontend_framework"] = "angular"
            elif "vue" in deps or "nuxt" in deps:
                stack["frontend_framework"] = "vue"
            elif "svelte" in deps:
                stack["frontend_framework"] = "svelte"
            else:
                stack["frontend_framework"] = "node"
            break

    # Backend
    for rp in (be / "requirements.txt", workspace / "requirements.txt",
               workspace / "pyproject.toml", workspace / "backend" / "pyproject.toml"):
        if rp.exists():
            try:
                txt = rp.read_text("utf-8", "replace").lower()
            except Exception:
                continue
            stack["has_backend"] = True
            if "fastapi" in txt:
                stack["backend_framework"] = "fastapi"
            elif "flask" in txt:
                stack["backend_framework"] = "flask"
            elif "django" in txt:
                stack["backend_framework"] = "django"
            elif "starlette" in txt:
                stack["backend_framework"] = "starlette"
            else:
                stack["backend_framework"] = "python"
            if "sqlalchemy" in txt:
                stack["has_db"] = True
                stack["db_engine"] = "sqlalchemy"
            elif "motor" in txt or "pymongo" in txt:
                stack["has_db"] = True
                stack["db_engine"] = "mongodb"
            elif "psycopg" in txt:
                stack["has_db"] = True
                stack["db_engine"] = "postgres"
            elif "aiosqlite" in txt:
                stack["has_db"] = True
                stack["db_engine"] = "sqlite"
            break

    # Node-only backend (Express, Fastify, Hono, etc.) detection.
    if not stack["has_backend"]:
        pj_top = workspace / "package.json"
        if pj_top.exists():
            pj = _read_json(pj_top)
            deps = {**(pj.get("dependencies") or {}), **(pj.get("devDependencies") or {})}
            if "express" in deps:
                stack["has_backend"] = True
                stack["backend_framework"] = "express"
            elif "fastify" in deps:
                stack["has_backend"] = True
                stack["backend_framework"] = "fastify"
            elif "hono" in deps:
                stack["has_backend"] = True
                stack["backend_framework"] = "hono"

    # Languages by file extension.
    EXT_LANG = {
        ".py": "python", ".js": "javascript", ".jsx": "javascript",
        ".ts": "typescript", ".tsx": "typescript", ".vue": "javascript",
        ".rs": "rust", ".go": "go", ".java": "java", ".rb": "ruby",
        ".php": "php", ".cs": "csharp",
    }
    counts: dict[str, int] = {}
    for p in workspace.rglob("*"):
        if not p.is_file():
            continue
        if any(part in STRIP_DIRS for part in p.parts):
            continue
        e = p.suffix.lower()
        if e in EXT_LANG:
            counts[e] = counts.get(e, 0) + 1
    seen: set[str] = set()
    for ext, _ in sorted(counts.items(), key=lambda kv: -kv[1]):
        lang = EXT_LANG[ext]
        if lang not in seen:
            stack["languages"].append(lang)
            seen.add(lang)
    return stack


def architecture_from_stack(stack: dict[str, Any]) -> dict[str, Any]:
    fe = stack["has_frontend"]
    be = stack["has_backend"]
    db = stack["has_db"]
    reasoning: list[str] = []
    if fe:
        reasoning.append(
            f"detected frontend: {stack['frontend_framework']}" if stack["frontend_framework"]
            else "detected frontend"
        )
    if be:
        reasoning.append(
            f"detected backend: {stack['backend_framework']}" if stack["backend_framework"]
            else "detected backend"
        )
    if db:
        reasoning.append(f"detected database: {stack['db_engine']}")

    if fe and be and db:
        kind = "full_stack"
    elif fe and be:
        kind = "api_driven"
    elif fe and not be:
        kind = "frontend_only"
    elif be and db:
        kind = "backend_required"
    elif be:
        kind = "backend_required"
    else:
        kind = "full_stack"
        reasoning.append("no clear signal; defaulting to full_stack")

    return {
        "kind": kind,
        "reasoning": reasoning,
        "requires_backend": kind != "frontend_only",
        "requires_database": kind in {"full_stack", "backend_required", "db_backed"},
        "blocked": False,
        "block_reasons": [],
        "limited_prototype_accepted": False,
        "detected_from": "existing_files",
    }


# ---------- Plan synthesis ----------
_RX_FASTAPI = re.compile(
    r'@(?:app|router|[a-zA-Z_][a-zA-Z0-9_]*)\.(get|post|put|patch|delete)\(\s*["\']([^"\']+)["\']'
)
_RX_EXPRESS = re.compile(
    r'(?:app|router)\.(get|post|put|patch|delete)\(\s*["\']([^"\']+)["\']'
)


def synthesize_plan(workspace: Path, stack: dict[str, Any]) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    endpoints: list[dict[str, Any]] = []

    for p in sorted(workspace.rglob("*")):
        if not p.is_file():
            continue
        if any(part in STRIP_DIRS for part in p.parts):
            continue
        rel = p.relative_to(workspace).as_posix()
        if rel.endswith((".lock", ".log", ".sqlite", ".db", ".pyc")):
            continue
        try:
            size = p.stat().st_size
        except FileNotFoundError:
            continue
        if size > 200_000:
            continue
        files.append({"path": rel, "purpose": "existing"})
        if len(files) >= 200:
            break

    # FastAPI / Flask endpoint scan.
    py_root = workspace / "backend" if (workspace / "backend").exists() else workspace
    if py_root.exists():
        for pyfile in py_root.rglob("*.py"):
            if any(part in STRIP_DIRS for part in pyfile.parts):
                continue
            try:
                text = pyfile.read_text("utf-8", "replace")
            except Exception:
                continue
            for m in _RX_FASTAPI.finditer(text):
                endpoints.append({
                    "method": m.group(1).upper(), "path": m.group(2),
                    "file": pyfile.relative_to(workspace).as_posix(),
                })
                if len(endpoints) > 80:
                    break
            if len(endpoints) > 80:
                break

    # Express endpoint scan (only if py-scan came up empty).
    if not endpoints:
        js_root = workspace / "backend" if (workspace / "backend").exists() else workspace
        for jsfile in js_root.rglob("*.js"):
            if any(part in STRIP_DIRS for part in jsfile.parts):
                continue
            try:
                text = jsfile.read_text("utf-8", "replace")
            except Exception:
                continue
            for m in _RX_EXPRESS.finditer(text):
                endpoints.append({
                    "method": m.group(1).upper(), "path": m.group(2),
                    "file": jsfile.relative_to(workspace).as_posix(),
                })
                if len(endpoints) > 80:
                    break
            if len(endpoints) > 80:
                break

    return {
        "files": files,
        "endpoints": endpoints,
        "data_models": [],
        "stack": stack,
        "synthesized_from": "existing_workspace",
    }


# ---------- BRD-from-code (LLM, heavy tier) ----------
_BRD_FROM_CODE_SYSTEM = """You are reverse-engineering a Business Requirements Document (BRD)
from an EXISTING software project. You are given the deterministic stack detection,
the file tree, and selected source files. Infer what the product IS, who uses it,
and what requirements it satisfies.

Be HONEST. If a feature looks half-built or unclear, mark it 'partial'. If a typical
app like this would have a feature but the code clearly doesn't, mark it 'unsupported'.
Never invent endpoints, data models, or tables that aren't visible in the code.

Return STRICT JSON — no markdown, no commentary:

{
  "product_name": "<short name>",
  "description": "<2-4 sentences>",
  "target_users": ["<persona>", "<persona>"],
  "requirements": [
    {"id": "R1", "text": "<short requirement>",
     "detail": "<one-line detail>",
     "status": "implemented|partial|unsupported"}
  ],
  "non_functional": ["<e.g., offline-first>"],
  "constraints": ["<observed constraints>"],
  "tech_stack": {"frontend":"...","backend":"...","db":"..."},
  "maturity_estimate": 0-100,
  "notes": "<honest observations: half-built features, dead code, integration TODOs>"
}
"""


def _tree(workspace: Path, limit: int = 300) -> list[str]:
    out: list[str] = []
    for p in sorted(workspace.rglob("*")):
        if any(part in STRIP_DIRS for part in p.parts):
            continue
        rel = p.relative_to(workspace)
        if len(out) >= limit:
            break
        out.append(rel.as_posix() + ("/" if p.is_dir() else ""))
    return out


def _select_sources(
    workspace: Path,
    max_files: int = 16,
    max_total_chars: int = 38_000,
) -> dict[str, str]:
    candidates = [
        "README.md", "README", "readme.md", "Readme.md",
        "backend/main.py", "backend/app.py", "backend/server.py",
        "backend/models.py", "backend/schemas.py",
        "backend/database.py", "backend/db.py",
        "backend/routes.py", "backend/api.py",
        "frontend/src/App.jsx", "frontend/src/App.js",
        "frontend/src/main.jsx", "frontend/src/main.js",
        "frontend/src/api.js", "frontend/src/index.js",
        "frontend/package.json", "backend/requirements.txt",
        "package.json", "requirements.txt",
        "frontend/vite.config.js", "frontend/index.html",
        "main.py", "app.py", "server.py",
    ]
    out: dict[str, str] = {}
    total = 0
    for rel in candidates:
        p = workspace / rel
        if not p.exists() or not p.is_file():
            continue
        try:
            text = p.read_text("utf-8", "replace")
        except Exception:
            continue
        if len(text) > 8000:
            text = text[:8000] + "\n# ...(truncated)\n"
        if total + len(text) > max_total_chars:
            break
        out[rel] = text
        total += len(text)
        if len(out) >= max_files:
            break

    # Top up with remaining backend python files if we still have room.
    be = workspace / "backend"
    if be.exists() and len(out) < max_files:
        for p in be.rglob("*.py"):
            if any(part in STRIP_DIRS for part in p.parts):
                continue
            rel = p.relative_to(workspace).as_posix()
            if rel in out:
                continue
            try:
                text = p.read_text("utf-8", "replace")
            except Exception:
                continue
            if len(text) > 6000:
                text = text[:6000] + "\n# ...(truncated)\n"
            if total + len(text) > max_total_chars:
                break
            out[rel] = text
            total += len(text)
            if len(out) >= max_files:
                break
    return out


async def derive_brd_from_code(
    gateway: LLMGateway,
    workspace: Path,
    stack: dict[str, Any],
) -> dict[str, Any]:
    tree = _tree(workspace, limit=300)
    sources = _select_sources(workspace)
    src_block = "\n\n".join(
        f"### {p}\n```\n{c}\n```" for p, c in sources.items()
    )
    user = (
        f"# Detected stack (deterministic, do not contradict)\n"
        f"```json\n{json.dumps(stack, indent=2)}\n```\n\n"
        f"# File tree (top {min(len(tree), 200)} entries)\n"
        f"```\n{chr(10).join(tree[:200])}\n```\n\n"
        f"# Selected source files (truncated where huge)\n{src_block}\n\n"
        "Return the BRD JSON as specified."
    )
    resp = await gateway.complete(
        system=_BRD_FROM_CODE_SYSTEM,
        user=user,
        json_mode=True,
        temperature=0.1,
        max_output_tokens=6000,
        tier="heavy",  # holistic reverse-engineering -> gemini-2.5-pro
    )
    obj = resp.as_json()
    if not isinstance(obj, dict):
        raise LLMError("brd_from_code returned non-dict")
    return obj


# ---------- Orchestrator ----------
async def ingest_to_project(
    workspace: Path,
    source_info: str,
    gateway: LLMGateway,
) -> dict[str, Any]:
    """Run stack/arch/plan detection + BRD inference on an already-populated workspace."""
    workspace = Path(workspace)
    out: dict[str, Any] = {
        "brd": {}, "architecture": {}, "plan": {},
        "stack": {}, "warnings": [], "error": "",
        "source": source_info,
    }
    stack = detect_stack(workspace)
    out["stack"] = stack
    out["architecture"] = architecture_from_stack(stack)
    out["plan"] = synthesize_plan(workspace, stack)

    try:
        brd = await derive_brd_from_code(gateway, workspace, stack)
        out["brd"] = brd
    except Exception as e:
        logger.warning("BRD inference failed: %s", e)
        out["error"] = f"brd_inference_failed: {type(e).__name__}: {str(e)[:200]}"
        out["brd"] = {
            "product_name": "Imported project",
            "description": "Auto-inference of BRD failed; please fill manually.",
            "requirements": [],
            "tech_stack": {
                "frontend": stack.get("frontend_framework", ""),
                "backend": stack.get("backend_framework", ""),
                "db": stack.get("db_engine", ""),
            },
            "maturity_estimate": 30,
            "notes": out["error"],
        }
    return out
