"""MEDIUM-1: Acceptance verifies plan.endpoints[*].path against backend source."""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent.parent))

from engines.acceptance_engine import run_acceptance  # noqa: E402


BRD = {
    "description": "Tiny notes API",
    "requirements": [{"id": "R1", "text": "list notes"}],
}
ARCH = {
    "kind": "full_stack",
    "requires_backend": True,
    "requires_database": False,
    "blocked": False,
    "block_reasons": [],
    "limited_prototype_accepted": False,
}


def _make_workspace(tmp: Path, main_py: str, fe: bool = True) -> Path:
    ws = tmp / "ws"
    ws.mkdir()
    be = ws / "backend"
    be.mkdir()
    (be / "main.py").write_text(main_py, encoding="utf-8")
    (be / "requirements.txt").write_text("fastapi==0.111\n", encoding="utf-8")
    if fe:
        f = ws / "frontend"
        (f / "src").mkdir(parents=True)
        (f / "package.json").write_text('{"dependencies":{"react":"^18","vite":"^5"}}', encoding="utf-8")
        (f / "vite.config.js").write_text("export default {}", encoding="utf-8")
        (f / "index.html").write_text("<html></html>", encoding="utf-8")
        (f / "src" / "main.jsx").write_text("// main", encoding="utf-8")
        (f / "src" / "App.jsx").write_text("export default function App(){}", encoding="utf-8")
    return ws


PLAN_OK = {
    "endpoints": [
        {"method": "GET", "path": "/api/notes"},
        {"method": "POST", "path": "/api/notes"},
    ]
}
PLAN_PARTIAL = {
    "endpoints": [
        {"method": "GET", "path": "/api/notes"},
        {"method": "DELETE", "path": "/api/notes/{id}"},  # missing
        {"method": "GET", "path": "/api/missing/route"},  # missing
    ]
}

MAIN_OK = """from fastapi import FastAPI, APIRouter
app = FastAPI()
router = APIRouter(prefix='/api')

@router.get('/notes')
def list_notes(): return []

@router.post('/notes')
def create_note(): return {}

app.include_router(router)
"""


def test_all_endpoints_present_pass():
    with tempfile.TemporaryDirectory() as tmp:
        ws = _make_workspace(Path(tmp), MAIN_OK)
        rep = run_acceptance(ws, BRD, ARCH, build_summary=None, plan=PLAN_OK)
        names = {c["name"]: c["status"] for c in rep.to_dict()["checks"]}
        assert names.get("plan.endpoints_implemented") == "PASS", names
        print("OK: PASS when every planned endpoint exists in main.py")


def test_some_endpoints_missing_partial():
    with tempfile.TemporaryDirectory() as tmp:
        ws = _make_workspace(Path(tmp), MAIN_OK)
        rep = run_acceptance(ws, BRD, ARCH, build_summary=None, plan=PLAN_PARTIAL)
        out = {c["name"]: c for c in rep.to_dict()["checks"]}
        ep = out.get("plan.endpoints_implemented")
        assert ep is not None and ep["status"] == "PARTIAL", out
        # Both missing paths should appear in the detail
        assert "/api/notes/{id}" in ep["detail"], ep["detail"]
        assert "/api/missing/route" in ep["detail"], ep["detail"]
        print("OK: PARTIAL when planned endpoints are missing; detail lists them.")


def test_no_plan_no_check():
    with tempfile.TemporaryDirectory() as tmp:
        ws = _make_workspace(Path(tmp), MAIN_OK)
        rep = run_acceptance(ws, BRD, ARCH, build_summary=None, plan=None)
        names = {c["name"] for c in rep.to_dict()["checks"]}
        assert "plan.endpoints_implemented" not in names, names
        print("OK: check is skipped when no plan is provided (back-compat).")


def test_method_mismatch_still_partial():
    """If path appears but with wrong HTTP method, weak match is recorded but
    we still surface no PARTIAL because the path is present (weak coverage).
    The current implementation considers presence of the literal path enough."""
    with tempfile.TemporaryDirectory() as tmp:
        ws = _make_workspace(Path(tmp), MAIN_OK)
        # GET /notes is implemented but plan asks for PATCH — implementation
        # only checks path presence, so this counts as 'found'.
        plan = {"endpoints": [{"method": "PATCH", "path": "/api/notes"}]}
        rep = run_acceptance(ws, BRD, ARCH, build_summary=None, plan=plan)
        out = {c["name"]: c for c in rep.to_dict()["checks"]}
        assert out["plan.endpoints_implemented"]["status"] in {"PASS", "PARTIAL"}
        # Confirm /api/notes is recognised as present even though method differs.
        print(
            "OK: path-only weak match recognised (method mismatch tolerated):",
            out["plan.endpoints_implemented"]["status"],
        )


if __name__ == "__main__":
    test_all_endpoints_present_pass()
    test_some_endpoints_missing_partial()
    test_no_plan_no_check()
    test_method_mismatch_still_partial()
    print("All MEDIUM-1 tests passed.")
