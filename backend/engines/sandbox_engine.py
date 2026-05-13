"""Sandbox engine: run a generated app in-place so the user can poke at it.

Lifecycle:
  start(project_id, workspace)  -> spawn `python -m uvicorn main:app --port P`
                                   in `workspace/backend`, return {pid, port}
  stop(project_id)              -> SIGTERM the process and free the port
  status(project_id)            -> {running, port, started_at, last_used}
  proxy_api(project_id, ...)    -> forward an HTTP call to the sandbox backend
  serve_static(project_id, ...) -> serve files from `workspace/frontend/dist`
                                   with the absolute string `/api/` rewritten
                                   so the frontend's same-origin API calls
                                   land back on the sandbox proxy.

Notes
-----
* One sandbox per project. Calling start() twice returns the existing entry.
* Reaper: an idle sandbox (no traffic for IDLE_LIMIT_S) is stopped on the next
  status check. Cap: MAX_SANDBOXES concurrent across all projects.
* All sandboxes are killed on cockpit shutdown (atexit).
* The catch-all route serves files from `frontend/dist`. The user must have
  successfully built the project first.
* For JS/HTML/CSS responses we do an in-memory string-replace:
      "/api/" -> "/api/sandbox/{id}/api/"
      '/api/' -> '/api/sandbox/{id}/api/'
  This is a deliberate hack: it lets us run the existing generated frontends
  without recompiling them. It targets the literal API base most generators
  emit (relative `/api/...` paths). For any binary file (images, fonts, etc.)
  the body is returned untouched.
"""
from __future__ import annotations

import atexit
import logging
import os
import socket
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

IDLE_LIMIT_S = 15 * 60          # auto-stop after 15 min of no activity
MAX_SANDBOXES = 3               # cap to keep the cockpit responsive
PORT_RANGE = (18000, 18100)


class SandboxError(RuntimeError):
    pass


class _SandboxRegistry:
    def __init__(self) -> None:
        self._entries: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()
        atexit.register(self.stop_all)

    # ------------------------------------------------------------------ utils
    def _find_free_port(self) -> int:
        with self._lock:
            taken = {e["port"] for e in self._entries.values()}
            for p in range(PORT_RANGE[0], PORT_RANGE[1]):
                if p in taken:
                    continue
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    try:
                        s.bind(("127.0.0.1", p))
                    except OSError:
                        continue
                return p
        raise SandboxError("no_free_port")

    @staticmethod
    def _wait_until_open(port: int, timeout_s: float = 10.0) -> bool:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.3)
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    return True
            time.sleep(0.25)
        return False

    # ------------------------------------------------------------- lifecycle
    def start(self, project_id: str, workspace: Path) -> dict[str, Any]:
        with self._lock:
            existing = self._entries.get(project_id)
            if existing and existing["process"].poll() is None:
                existing["last_used"] = time.time()
                return self._public(existing)

            # Cap on concurrent sandboxes — stop the least-recently-used.
            self._reap_idle_locked()
            while len(self._entries) >= MAX_SANDBOXES:
                victim = min(self._entries.items(), key=lambda kv: kv[1]["last_used"])
                logger.warning("Sandbox cap reached (%d); evicting LRU project=%s",
                               MAX_SANDBOXES, victim[0])
                self._stop_locked(victim[0])

            # Preconditions on workspace.
            backend = workspace / "backend"
            main_py = backend / "main.py"
            dist = workspace / "frontend" / "dist"
            if not main_py.exists():
                raise SandboxError("backend_main_missing")
            if not dist.exists():
                raise SandboxError("frontend_dist_missing")

            port = self._find_free_port()
            log_dir = workspace / ".factory"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / f"sandbox-{port}.log"
            log_fh = open(log_path, "w", buffering=1)
            log_fh.write(f"[sandbox] starting on port {port} at {time.ctime()}\n")
            log_fh.flush()

            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            # Reset DATABASE_URL/MONGO_URL to NOT inherit the cockpit's own —
            # the generated app should use its own .env via load_dotenv().
            for key in ("MONGO_URL", "DB_NAME", "DATABASE_URL"):
                env.pop(key, None)

            cmd = [
                "python", "-m", "uvicorn",
                "main:app",
                "--host", "127.0.0.1",
                "--port", str(port),
                "--log-level", "warning",
            ]
            try:
                proc = subprocess.Popen(
                    cmd, cwd=str(backend), env=env,
                    stdout=log_fh, stderr=subprocess.STDOUT,
                    start_new_session=True,  # so we can SIGTERM the whole group
                )
            except Exception as e:
                log_fh.close()
                raise SandboxError(f"spawn_failed: {e}") from e

            if not self._wait_until_open(port, timeout_s=10.0):
                # Capture tail of log for the caller
                try:
                    proc.terminate()
                    proc.wait(timeout=2)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                log_fh.close()
                tail = log_path.read_text("utf-8", "replace").splitlines()[-30:]
                raise SandboxError("backend_did_not_open_port: " + "\n".join(tail))

            entry = {
                "project_id": project_id,
                "process": proc,
                "log_fh": log_fh,
                "port": port,
                "log_path": str(log_path),
                "workspace": str(workspace),
                "dist_dir": str(dist),
                "started_at": time.time(),
                "last_used": time.time(),
            }
            self._entries[project_id] = entry
            logger.info("Sandbox started: project=%s port=%d pid=%d", project_id, port, proc.pid)
            return self._public(entry)

    def _stop_locked(self, project_id: str) -> bool:
        entry = self._entries.pop(project_id, None)
        if not entry:
            return False
        proc = entry["process"]
        try:
            proc.terminate()
            proc.wait(timeout=4)
        except subprocess.TimeoutExpired:
            try:
                proc.kill()
            except Exception:
                pass
        except Exception:
            pass
        try:
            entry["log_fh"].close()
        except Exception:
            pass
        logger.info("Sandbox stopped: project=%s port=%d", project_id, entry["port"])
        return True

    def stop(self, project_id: str) -> bool:
        with self._lock:
            return self._stop_locked(project_id)

    def stop_all(self) -> None:
        with self._lock:
            for pid in list(self._entries.keys()):
                self._stop_locked(pid)

    def _reap_idle_locked(self) -> None:
        now = time.time()
        idle = [pid for pid, e in self._entries.items() if (now - e["last_used"]) > IDLE_LIMIT_S]
        for pid in idle:
            logger.info("Reaping idle sandbox: %s", pid)
            self._stop_locked(pid)

    # ------------------------------------------------------------ inspection
    def get(self, project_id: str) -> Optional[dict[str, Any]]:
        with self._lock:
            self._reap_idle_locked()
            entry = self._entries.get(project_id)
            if not entry:
                return None
            if entry["process"].poll() is not None:
                # process died — drop it
                self._stop_locked(project_id)
                return None
            return entry

    def public(self, project_id: str) -> Optional[dict[str, Any]]:
        e = self.get(project_id)
        return self._public(e) if e else None

    def list_all(self) -> list[dict[str, Any]]:
        with self._lock:
            self._reap_idle_locked()
            return [self._public(e) for e in self._entries.values()]

    def touch(self, project_id: str) -> None:
        with self._lock:
            e = self._entries.get(project_id)
            if e:
                e["last_used"] = time.time()

    @staticmethod
    def _public(entry: dict[str, Any]) -> dict[str, Any]:
        return {
            "project_id": entry["project_id"],
            "port": entry["port"],
            "pid": entry["process"].pid,
            "started_at": entry["started_at"],
            "last_used": entry["last_used"],
            "log_path": entry["log_path"],
            "alive": entry["process"].poll() is None,
            "sandbox_url": f"/api/sandbox/{entry['project_id']}/",
        }

    def log_tail(self, project_id: str, lines: int = 80) -> str:
        e = self.get(project_id)
        if not e:
            return ""
        try:
            text = Path(e["log_path"]).read_text("utf-8", "replace")
        except Exception:
            return ""
        return "\n".join(text.splitlines()[-lines:])


REGISTRY = _SandboxRegistry()


def rewrite_api_base_for_sandbox(body: bytes, content_type: str, project_id: str) -> bytes:
    """Rewrite absolute path references so a generated app works inside the
    sandbox URL prefix `/api/sandbox/{project_id}/`.

    Two distinct rewrites:
      * Universal (all text resources):
            "/api/"   -> "/api/sandbox/{id}/api/"
            '/api/'   -> '/api/sandbox/{id}/api/'
            `/api/`   -> `/api/sandbox/{id}/api/`
        This routes the generated frontend's same-origin API calls back
        through the cockpit's proxy.

      * HTML only:
            src/href="/assets/..."  -> src/href="assets/..."
            src/href="/vite.svg"    -> src/href="vite.svg"   (and friends)
            <head>...</head>        -> <base href="/api/sandbox/{id}/">…</head>
        Makes absolute-rooted asset references resolve under the sandbox URL.

    Binary content types are returned unchanged.
    """
    ct = (content_type or "").lower()
    if not any(t in ct for t in ("html", "javascript", "json", "css", "text", "xml", "svg")):
        return body
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        return body

    target = f"/api/sandbox/{project_id}/api/"
    text = (
        text
        .replace('"/api/', '"' + target)
        .replace("'/api/", "'" + target)
        .replace("`/api/", "`" + target)
    )

    # HTML-only: rewrite absolute asset paths and inject <base>.
    if "html" in ct:
        import re as _re
        # 1) src/href="/anything" (any leading slash absolute path) -> "anything"
        #    — but only outside of full URLs (http://) and only when it points
        #    to a static asset path (assets, favicon, *.svg, *.png, etc.).
        text = _re.sub(
            r'((?:src|href)\s*=\s*["\'])/(?!/|api/)([^"\']*?["\'])',
            r'\1\2',
            text,
        )
        # 2) Insert <base> right after <head> open tag so relative URLs resolve
        #    against the sandbox path.
        base_tag = f'<base href="/api/sandbox/{project_id}/">'
        if base_tag not in text:
            text = _re.sub(r'(<head(?:\s[^>]*)?>)', r'\1\n    ' + base_tag, text, count=1, flags=_re.IGNORECASE)

    return text.encode("utf-8")
