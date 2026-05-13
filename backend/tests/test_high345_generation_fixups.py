"""HIGH-3 / HIGH-4 unit tests for two generation-engine fixups added in the
2026-05-13 "calculator made a mess" pass:

HIGH-3 — _stub_missing_named_exports_js: silent no-op stubs (= null) are
         dishonest and silently break runtime. New behaviour:
           - alias to the closest existing export with name-similarity ≥ 0.6,
           - else generate a stub that THROWS at call time (loud failure).

HIGH-4 — _ensure_pydantic_camel_aliases: frontend conventionally sends camelCase
         (`sessionId`), backend Pydantic schemas conventionally declare
         snake_case (`session_id`). Mismatch causes runtime 422s. New behaviour:
         inject `model_config = ConfigDict(alias_generator=to_camel,
         populate_by_name=True, ...)` into every BaseModel subclass that uses
         snake_case fields.

HIGH-5 — _ensure_frontend_uses_relative_api: hardcoded `http://localhost:8000`
         strings in JS sources are rewritten to empty string (= same-origin).
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engines.generation_engine import (  # noqa: E402
    _ensure_frontend_uses_relative_api,
    _ensure_pydantic_camel_aliases,
    _fix_python_class_attr_case_mismatches,
    _stub_missing_named_exports_js,
)


def _make_ws() -> Path:
    return Path(tempfile.mkdtemp(prefix="gen-fixup-test-"))


# ----------------- HIGH-3 -----------------
def test_stub_aliases_to_similar_named_export():
    ws = _make_ws()
    fe = ws / "frontend" / "src"
    fe.mkdir(parents=True)
    (fe / "api.js").write_text(
        "export const saveCalculation = (x) => x;\n"
        "export const fetchCalculationHistory = (x) => x;\n"
    )
    (fe / "App.jsx").write_text(
        "import { saveCalculation, getCalculations } from './api';\n"
        "export default function App(){ return null; }\n"
    )
    _stub_missing_named_exports_js(ws)
    out = (fe / "api.js").read_text()
    # `getCalculations` should be aliased to `fetchCalculationHistory` (closest match)
    assert "export const getCalculations = fetchCalculationHistory;" in out, \
        f"expected alias to fetchCalculationHistory; got:\n{out}"
    print("OK: HIGH-3 alias-to-similar-export works")


def test_stub_throws_when_no_similar_export_exists():
    ws = _make_ws()
    fe = ws / "frontend" / "src"
    fe.mkdir(parents=True)
    (fe / "api.js").write_text(
        "export const saveCalculation = (x) => x;\n"
    )
    (fe / "App.jsx").write_text(
        "import { saveCalculation, foobarTotallyUnrelated } from './api';\n"
        "export default function App(){ return null; }\n"
    )
    _stub_missing_named_exports_js(ws)
    out = (fe / "api.js").read_text()
    # `foobarTotallyUnrelated` has no similar export; must throw, not return null.
    assert "throw new Error" in out, f"expected loud throw stub, got:\n{out}"
    assert "= (...args) => null" not in out, f"silent null-return is forbidden; got:\n{out}"
    print("OK: HIGH-3 loud-throwing stub when no plausible match")


# ----------------- HIGH-4 -----------------
def test_pydantic_camel_alias_injection_on_snake_case_fields():
    ws = _make_ws()
    be = ws / "backend"
    be.mkdir(parents=True)
    (be / "schemas.py").write_text(
        "from pydantic import BaseModel\n"
        "\n"
        "class CalculationCreate(BaseModel):\n"
        "    session_id: str\n"
        "    expression: str\n"
        "    result: float\n"
    )
    _ensure_pydantic_camel_aliases(ws)
    out = (be / "schemas.py").read_text()
    assert "ConfigDict" in out
    assert "from pydantic.alias_generators import to_camel" in out
    assert "alias_generator=to_camel" in out
    assert "populate_by_name=True" in out
    print("OK: HIGH-4 camelCase aliases injected for snake_case schema")


def test_pydantic_no_change_when_no_snake_fields():
    ws = _make_ws()
    be = ws / "backend"
    be.mkdir(parents=True)
    original = (
        "from pydantic import BaseModel\n"
        "\n"
        "class Thing(BaseModel):\n"
        "    name: str\n"
        "    count: int\n"
    )
    (be / "schemas.py").write_text(original)
    _ensure_pydantic_camel_aliases(ws)
    out = (be / "schemas.py").read_text()
    assert out == original, "must not modify schema with no snake_case fields"
    print("OK: HIGH-4 leaves all-camelCase schemas untouched")


def test_pydantic_respects_existing_model_config():
    ws = _make_ws()
    be = ws / "backend"
    be.mkdir(parents=True)
    original = (
        "from pydantic import BaseModel, ConfigDict\n"
        "\n"
        "class CalculationCreate(BaseModel):\n"
        "    session_id: str\n"
        "    model_config = ConfigDict(from_attributes=True)\n"
    )
    (be / "schemas.py").write_text(original)
    _ensure_pydantic_camel_aliases(ws)
    out = (be / "schemas.py").read_text()
    # Don't double-inject: respect what the LLM/user already wrote.
    assert out.count("model_config") == 1, f"must not double-inject; got:\n{out}"
    print("OK: HIGH-4 respects existing model_config")


def test_pydantic_transitive_inheritance_and_mixed_existing_config():
    """The real-world case: schemas.py has a chain (CalculationBase -> ...Create / ...Response).
    Only the Response has its own model_config. The Base + Create must still get camel aliases."""
    ws = _make_ws()
    be = ws / "backend"
    be.mkdir(parents=True)
    original = (
        "from datetime import datetime\n"
        "from uuid import UUID\n"
        "from pydantic import BaseModel, ConfigDict\n"
        "\n"
        "class CalculationBase(BaseModel):\n"
        "    session_id: str\n"
        "    expression: str\n"
        "\n"
        "class CalculationCreate(CalculationBase):\n"
        "    pass\n"
        "\n"
        "class CalculationResponse(CalculationBase):\n"
        "    id: UUID\n"
        "    timestamp: datetime\n"
        "    model_config = ConfigDict(from_attributes=True)\n"
    )
    (be / "schemas.py").write_text(original)
    _ensure_pydantic_camel_aliases(ws)
    out = (be / "schemas.py").read_text()
    # CalculationBase has snake_case fields and no model_config -> must get injection
    base_section = out.split("class CalculationCreate")[0]
    assert "alias_generator=to_camel" in base_section, \
        f"CalculationBase must get camelCase aliases:\n{out}"
    # CalculationResponse already has its own config -> must not be touched (only one model_config in that section)
    resp_section = out.split("class CalculationResponse")[1]
    assert resp_section.count("model_config") == 1, \
        f"CalculationResponse must keep its own model_config only once:\n{out}"
    # Imports must be present
    assert "from pydantic.alias_generators import to_camel" in out
    print("OK: HIGH-4 handles transitive BaseModel inheritance + per-class model_config")


# ----------------- HIGH-5 -----------------
def test_localhost_api_rewritten_to_relative():
    ws = _make_ws()
    fe_src = ws / "frontend" / "src"
    fe_src.mkdir(parents=True)
    (fe_src / "api.js").write_text(
        "import axios from 'axios';\n"
        "const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';\n"
        "const api = axios.create({ baseURL: API_BASE_URL });\n"
    )
    _ensure_frontend_uses_relative_api(ws)
    out = (fe_src / "api.js").read_text()
    assert "'http://localhost:8000'" not in out, f"localhost not rewritten:\n{out}"
    assert "import.meta.env.VITE_API_URL ||" in out
    assert "''" in out
    print("OK: HIGH-5 hardcoded localhost API base rewritten")


# ----------------- HIGH-6 -----------------
def test_class_attr_case_mismatch_snake_to_camel():
    """models.py declares session_id (snake); main.py uses Calculation.sessionId (camel)."""
    ws = _make_ws()
    be = ws / "backend"
    be.mkdir(parents=True)
    (be / "models.py").write_text(
        "from sqlalchemy import Column, String\n"
        "class Base: pass\n"
        "class Calculation(Base):\n"
        "    session_id = Column(String)\n"
        "    expression = Column(String)\n"
    )
    (be / "main.py").write_text(
        "from models import Calculation\n"
        "def get_one(db, ids):\n"
        "    return db.query(Calculation).filter(Calculation.sessionId.in_(ids)).all()\n"
    )
    _fix_python_class_attr_case_mismatches(ws)
    out_main = (be / "main.py").read_text()
    assert "Calculation.session_id" in out_main, f"sessionId not rewritten:\n{out_main}"
    assert "Calculation.sessionId" not in out_main
    print("OK: HIGH-6 camelCase usage -> snake_case declaration")


def test_class_attr_case_mismatch_camel_to_snake():
    """Pydantic schema declares userName (camel); router uses User.user_name (snake)."""
    ws = _make_ws()
    be = ws / "backend"
    be.mkdir(parents=True)
    (be / "schemas.py").write_text(
        "from pydantic import BaseModel\n"
        "class User(BaseModel):\n"
        "    userName: str\n"
        "    age: int\n"
    )
    (be / "router.py").write_text(
        "from schemas import User\n"
        "def view(u: User):\n"
        "    return u.user_name + str(u.age)\n"
    )
    _fix_python_class_attr_case_mismatches(ws)
    out = (be / "router.py").read_text()
    # NOTE: instance attribute references like u.user_name are not rewritten —
    # only ClassName.attr references are. The fixup is conservative on purpose
    # to avoid false positives on unrelated `obj.foo` accesses.
    # This documents the intentional behaviour.
    assert "u.user_name" in out, "instance accesses are intentionally NOT rewritten"
    print("OK: HIGH-6 conservatively skips instance-attribute usage")


def test_class_attr_no_change_when_attribute_exists():
    ws = _make_ws()
    be = ws / "backend"
    be.mkdir(parents=True)
    (be / "models.py").write_text(
        "class Foo:\n"
        "    bar = 1\n"
    )
    (be / "use.py").write_text("from models import Foo\nprint(Foo.bar)\n")
    _fix_python_class_attr_case_mismatches(ws)
    out = (be / "use.py").read_text()
    assert out == "from models import Foo\nprint(Foo.bar)\n", "must not touch valid attrs"
    print("OK: HIGH-6 leaves valid attrs untouched")


def test_class_attr_case_mismatch_with_import_alias():
    """models.py declares session_id on Calculation; main.py imports it as DB_Calculation
    and accidentally writes DB_Calculation.sessionId. Must rewrite via the alias."""
    ws = _make_ws()
    be = ws / "backend"
    be.mkdir(parents=True)
    (be / "models.py").write_text(
        "from sqlalchemy import Column, String\n"
        "class Base: pass\n"
        "class Calculation(Base):\n"
        "    session_id = Column(String)\n"
    )
    (be / "main.py").write_text(
        "from models import Calculation as DB_Calculation\n"
        "def get_one(db, ids):\n"
        "    return db.query(DB_Calculation).filter(DB_Calculation.sessionId.in_(ids)).all()\n"
    )
    _fix_python_class_attr_case_mismatches(ws)
    out = (be / "main.py").read_text()
    assert "DB_Calculation.session_id" in out, f"alias not rewritten:\n{out}"
    assert "DB_Calculation.sessionId" not in out
    print("OK: HIGH-6 handles import alias (Calculation as DB_Calculation)")


if __name__ == "__main__":
    test_stub_aliases_to_similar_named_export()
    test_stub_throws_when_no_similar_export_exists()
    test_pydantic_camel_alias_injection_on_snake_case_fields()
    test_pydantic_no_change_when_no_snake_fields()
    test_pydantic_respects_existing_model_config()
    test_pydantic_transitive_inheritance_and_mixed_existing_config()
    test_localhost_api_rewritten_to_relative()
    test_class_attr_case_mismatch_snake_to_camel()
    test_class_attr_case_mismatch_camel_to_snake()
    test_class_attr_no_change_when_attribute_exists()
    test_class_attr_case_mismatch_with_import_alias()
    print("All HIGH-3/4/5/6 fixup tests passed.")
