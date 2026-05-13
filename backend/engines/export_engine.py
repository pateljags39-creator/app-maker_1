"""Export engine: produce clean distributable ZIP excluding secrets/build artifacts."""
from __future__ import annotations

import hashlib
import json
import time
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

EXCLUDE_DIRS = {
    "node_modules", "__pycache__", ".venv", "venv", ".pytest_cache", "dist",
    "build", ".factory", ".git", ".cache", ".next", ".mypy_cache", ".ruff_cache",
}
EXCLUDE_FILES = {
    ".env", ".env.local", ".env.production", ".env.staging",
    "secrets.json", "id_rsa", "id_rsa.pub",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".log"}

SECRET_PATTERNS = [
    r"AIza[0-9A-Za-z_-]{30,}",  # Google API keys
    r"sk-[A-Za-z0-9_-]{20,}",   # OpenAI / Emergent
    r"ghp_[A-Za-z0-9]{30,}",    # GitHub PAT
    r"AKIA[0-9A-Z]{16}",        # AWS Access Key
]


@dataclass
class ExportRecord:
    path: str
    sha256: str
    files: int
    size_bytes: int
    secret_findings: int
    created_at: float
    manifest_path: str


def _should_include(rel: Path) -> bool:
    parts = set(rel.parts)
    if parts & EXCLUDE_DIRS:
        return False
    if rel.name in EXCLUDE_FILES:
        return False
    if rel.suffix in EXCLUDE_SUFFIXES:
        return False
    return True


def _scan_for_secrets(text: str) -> list[str]:
    import re
    found: list[str] = []
    for pat in SECRET_PATTERNS:
        for m in re.finditer(pat, text):
            # Mask before logging.
            tok = m.group(0)
            found.append(tok[:4] + "***" + tok[-3:])
    return found


def export_project(workspace: Path, out_dir: Path | None = None, project_name: str = "app") -> ExportRecord:
    workspace = Path(workspace)
    if not workspace.exists():
        raise FileNotFoundError(str(workspace))
    out_dir = Path(out_dir) if out_dir else workspace / ".factory" / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    zip_path = out_dir / f"{project_name}-{ts}.zip"

    sha = hashlib.sha256()
    files = 0
    size = 0
    secret_hits: list[dict[str, Any]] = []
    manifest_files: list[dict[str, Any]] = []

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(workspace.rglob("*")):
            rel = p.relative_to(workspace)
            if not _should_include(rel):
                continue
            if p.is_file():
                try:
                    data = p.read_bytes()
                except Exception:
                    continue
                # secret scan on text files only
                if p.suffix in {".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".html", ".css", ".yml", ".yaml", ".env"}:
                    try:
                        text = data.decode("utf-8", "replace")
                        found = _scan_for_secrets(text)
                        if found:
                            secret_hits.append({"file": rel.as_posix(), "matches": found})
                    except Exception:
                        pass
                sha.update(rel.as_posix().encode())
                sha.update(b"\x00")
                sha.update(data)
                files += 1
                size += len(data)
                manifest_files.append({"path": rel.as_posix(), "size": len(data)})
                zf.writestr(rel.as_posix(), data)

    manifest = {
        "project_name": project_name,
        "exported_at": ts,
        "file_count": files,
        "size_bytes": size,
        "sha256": sha.hexdigest(),
        "excluded_dirs": sorted(EXCLUDE_DIRS),
        "excluded_files": sorted(EXCLUDE_FILES),
        "excluded_suffixes": sorted(EXCLUDE_SUFFIXES),
        "secret_findings": secret_hits,
        "files": manifest_files[:500],  # cap for manifest size
        "files_truncated": len(manifest_files) > 500,
    }
    manifest_path = out_dir / f"{project_name}-{ts}.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    return ExportRecord(
        path=str(zip_path),
        sha256=sha.hexdigest(),
        files=files,
        size_bytes=size,
        secret_findings=len(secret_hits),
        created_at=float(ts),
        manifest_path=str(manifest_path),
    )
