"""Sandbox routes — run a generated project so the user can demo it.

Two route groups:

1. Lifecycle (mounted at /api/projects/{project_id}/sandbox):
     POST   start    -> spawn the generated backend; returns sandbox_url + port
     POST   stop     -> shut it down
     GET    status   -> running? port? started_at? last_used?
     GET    logs     -> tail of the sandbox backend's stdout/stderr

2. Serve / proxy (mounted at /api/sandbox/{project_id}):
     ANY  /*         -> if path begins with `api/`, proxy to the sandbox
                        backend; else serve the file from frontend/dist/ with
                        absolute `/api/` rewritten to `/api/sandbox/{id}/api/`.

The proxy is unauthenticated by design — same trust model as the cockpit
itself (single-user, local). It listens on the same /api/ prefix so it works
under the existing Kubernetes ingress without needing new rules.
"""
from __future__ import annotations

import logging
import mimetypes
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from starlette.responses import StreamingResponse

from engines.sandbox_engine import REGISTRY, SandboxError, rewrite_api_base_for_sandbox
from event_ledger import get_ledger
import repositories as repo

logger = logging.getLogger(__name__)

# Two routers — they get different prefixes when registered.
lifecycle_router = APIRouter(prefix="/projects", tags=["sandbox"])
proxy_router = APIRouter(prefix="/sandbox", tags=["sandbox"])


@lifecycle_router.post("/{project_id}/sandbox/start")
async def sandbox_start(project_id: str):
    doc = await repo.get_project(project_id)
    if not doc:
        raise HTTPException(404, "project_not_found")
    workspace = Path(doc.get("workspace_dir") or "")
    if not workspace.exists():
        raise HTTPException(409, "workspace_missing — run Generate + Build first")
    try:
        info = REGISTRY.start(project_id, workspace)
    except SandboxError as e:
        # Surface the actual reason so the UI can show it
        await get_ledger().emit_simple(
            project_id=project_id, type="sandbox.start_failed",
            message=f"Sandbox start failed: {e}",
            payload={"error": str(e)}, severity="error",
        )
        raise HTTPException(409, str(e)) from None
    await get_ledger().emit_simple(
        project_id=project_id, type="sandbox.started",
        message=f"Sandbox running on port {info['port']}",
        payload={"port": info["port"]}, severity="success",
    )
    return info


@lifecycle_router.post("/{project_id}/sandbox/stop")
async def sandbox_stop(project_id: str):
    stopped = REGISTRY.stop(project_id)
    if stopped:
        await get_ledger().emit_simple(
            project_id=project_id, type="sandbox.stopped",
            message="Sandbox stopped", payload={}, severity="info",
        )
    return {"stopped": stopped}


@lifecycle_router.get("/{project_id}/sandbox/status")
async def sandbox_status(project_id: str):
    info = REGISTRY.public(project_id)
    if not info:
        return {"running": False}
    return {"running": True, **info}


@lifecycle_router.get("/{project_id}/sandbox/logs")
async def sandbox_logs(project_id: str, lines: int = 80):
    return {"tail": REGISTRY.log_tail(project_id, lines=lines)}


# ---------------------------------------------------------------- proxy/serve
_PROXY_HEADER_DENYLIST = {
    "host", "content-length", "transfer-encoding", "connection",
    "keep-alive", "te", "trailers", "upgrade",
}


async def _proxy_to_backend(request: Request, port: int, sub_path: str) -> Response:
    """Forward `request` to http://127.0.0.1:{port}/{sub_path} verbatim."""
    target = f"http://127.0.0.1:{port}/{sub_path}"
    if request.url.query:
        target += f"?{request.url.query}"
    fwd_headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in _PROXY_HEADER_DENYLIST
    }
    body = await request.body()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.request(
                request.method, target,
                content=body if body else None,
                headers=fwd_headers,
            )
    except httpx.ConnectError:
        raise HTTPException(502, "sandbox_backend_unreachable") from None
    except httpx.ReadTimeout:
        raise HTTPException(504, "sandbox_backend_timeout") from None
    # Don't forward hop-by-hop headers back.
    out_headers = {
        k: v for k, v in r.headers.items()
        if k.lower() not in _PROXY_HEADER_DENYLIST
    }
    return Response(content=r.content, status_code=r.status_code, headers=out_headers,
                    media_type=r.headers.get("content-type"))


def _serve_static(dist_dir: Path, sub_path: str, project_id: str) -> Response:
    """Serve a file from `dist_dir/{sub_path}`, rewriting `/api/` refs in text."""
    if not sub_path or sub_path.endswith("/"):
        target = dist_dir / "index.html"
    else:
        target = (dist_dir / sub_path).resolve()
        # Path-traversal guard
        if not str(target).startswith(str(dist_dir.resolve())):
            raise HTTPException(403, "path_escape")
        if not target.exists() or not target.is_file():
            # SPA fallback
            target = dist_dir / "index.html"
    if not target.exists():
        raise HTTPException(404, "file_not_found")
    body = target.read_bytes()
    media_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
    rewritten = rewrite_api_base_for_sandbox(body, media_type, project_id)
    return Response(content=rewritten, media_type=media_type, headers={
        "Cache-Control": "no-cache, no-store, must-revalidate",
    })


@proxy_router.api_route(
    "/{project_id}/{full_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def sandbox_serve(project_id: str, full_path: str, request: Request):
    entry = REGISTRY.get(project_id)
    if not entry:
        # If they hit the root path with no sandbox running, return a friendly page.
        if full_path in {"", "/"}:
            html = (
                "<!doctype html><html><body style='font-family:system-ui;padding:2rem'>"
                "<h2>Sandbox not running</h2>"
                "<p>Click <strong>Run Demo</strong> in the cockpit to start it.</p>"
                "</body></html>"
            )
            return Response(content=html, media_type="text/html", status_code=409)
        raise HTTPException(409, "sandbox_not_running")
    REGISTRY.touch(project_id)

    # Route API calls to the sandbox backend; everything else is static.
    if full_path.startswith("api/") or full_path == "api":
        return await _proxy_to_backend(request, entry["port"], full_path)
    if request.method not in {"GET", "HEAD"}:
        # The static serve only handles GET. Anything else for a non-api path is an error.
        raise HTTPException(405, "method_not_allowed_on_static")
    dist = Path(entry["dist_dir"])
    return _serve_static(dist, full_path, project_id)


# Combined router for routes/__init__.py to import.
router = APIRouter()
router.include_router(lifecycle_router)
router.include_router(proxy_router)
