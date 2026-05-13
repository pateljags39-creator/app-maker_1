"""Snapshot engine: tar+gzip workspace into .factory/snapshots, with sha256 manifest."""
from __future__ import annotations

import hashlib
import json
import tarfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

EXCLUDE_DIRS = {"node_modules", "__pycache__", ".venv", "venv", ".pytest_cache", "dist", "build", ".factory", ".git"}
EXCLUDE_FILES = {".env", ".env.local", ".env.production"}


@dataclass
class Snapshot:
    id: str
    path: str
    sha256: str
    files: int
    size_bytes: int
    created_at: float
    label: str = ""


def _should_include(p: Path) -> bool:
    parts = set(p.parts)
    if parts & EXCLUDE_DIRS:
        return False
    if p.name in EXCLUDE_FILES:
        return False
    return True


def create_snapshot(workspace: Path, label: str = "") -> Snapshot:
    workspace = Path(workspace)
    if not workspace.exists():
        raise FileNotFoundError(str(workspace))
    snap_dir = workspace / ".factory" / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    snap_id = f"snap-{ts}"
    tar_path = snap_dir / f"{snap_id}.tar.gz"
    h = hashlib.sha256()
    file_count = 0
    size = 0
    with tarfile.open(tar_path, "w:gz") as tar:
        for p in sorted(workspace.rglob("*")):
            rel = p.relative_to(workspace)
            if not _should_include(rel):
                continue
            if p.is_file():
                with p.open("rb") as fh:
                    data = fh.read()
                h.update(rel.as_posix().encode())
                h.update(b"\x00")
                h.update(data)
                size += len(data)
                file_count += 1
                ti = tarfile.TarInfo(rel.as_posix())
                ti.size = len(data)
                import io
                tar.addfile(ti, io.BytesIO(data))
    snap = Snapshot(
        id=snap_id,
        path=str(tar_path),
        sha256=h.hexdigest(),
        files=file_count,
        size_bytes=size,
        created_at=float(ts),
        label=label,
    )
    manifest = snap_dir / f"{snap_id}.json"
    manifest.write_text(json.dumps(asdict(snap), indent=2))
    return snap


def list_snapshots(workspace: Path) -> list[Snapshot]:
    snap_dir = Path(workspace) / ".factory" / "snapshots"
    out: list[Snapshot] = []
    if not snap_dir.exists():
        return out
    for jf in sorted(snap_dir.glob("snap-*.json")):
        try:
            d = json.loads(jf.read_text())
            out.append(Snapshot(**d))
        except Exception:
            continue
    return out


def restore_snapshot(workspace: Path, snapshot_id: str) -> dict[str, Any]:
    workspace = Path(workspace)
    snap_dir = workspace / ".factory" / "snapshots"
    tar_path = snap_dir / f"{snapshot_id}.tar.gz"
    if not tar_path.exists():
        raise FileNotFoundError(str(tar_path))
    # Remove non-protected files from workspace before restore.
    for p in list(workspace.rglob("*")):
        rel = p.relative_to(workspace)
        if rel.parts and rel.parts[0] == ".factory":
            continue
        if p.is_file():
            try:
                p.unlink()
            except Exception:
                pass
    for p in sorted(workspace.rglob("*"), reverse=True):
        if p.is_dir() and not any(p.iterdir()):
            rel = p.relative_to(workspace)
            if rel.parts and rel.parts[0] == ".factory":
                continue
            try:
                p.rmdir()
            except Exception:
                pass
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(workspace)
    return {"restored": snapshot_id, "workspace": str(workspace)}
