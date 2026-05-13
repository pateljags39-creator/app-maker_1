"""Test HIGH-1: frontend_only + limited_prototype propagates `unsupported` to BRD reqs."""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent.parent))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(HERE.parent.parent / ".env")

from engines.architecture_engine import detect_architecture  # noqa: E402


def test_block_when_no_limited_prototype():
    brd = {
        "description": "Notes app with login.",
        "requirements": [
            {"id": "R1", "text": "Save notes to database"},
            {"id": "R2", "text": "Login with email"},
            {"id": "R3", "text": "View notes UI"},
        ],
        "forced_architecture": "frontend_only",
    }
    d = detect_architecture(brd, allow_limited_prototype=False).to_dict()
    assert d["blocked"] is True, "must block frontend_only when BRD needs backend"
    assert d["unsupported_requirement_indices"] == [], "must not list unsupported when blocked"
    print("OK: blocks frontend_only when BRD needs backend without ack")


def test_limited_prototype_marks_unsupported():
    brd = {
        "description": "Notes app with login.",
        "requirements": [
            {"id": "R1", "text": "Save notes to database"},
            {"id": "R2", "text": "Login with email"},
            {"id": "R3", "text": "View notes UI"},
        ],
        "forced_architecture": "frontend_only",
    }
    d = detect_architecture(brd, allow_limited_prototype=True).to_dict()
    assert d["blocked"] is False
    assert d["kind"] == "frontend_only"
    assert d["limited_prototype_accepted"] is True
    # R1 (database/save) and R2 (login) must be flagged unsupported; R3 must not.
    assert 0 in d["unsupported_requirement_indices"], "R1 (db) must be unsupported"
    assert 1 in d["unsupported_requirement_indices"], "R2 (login) must be unsupported"
    assert 2 not in d["unsupported_requirement_indices"], "R3 (UI only) must NOT be unsupported"
    assert len(d["unsupported_signal_keywords"]) > 0
    print("OK: limited_prototype flags backend reqs as unsupported:", d["unsupported_requirement_indices"])


def test_pure_frontend_brd_passes_clean():
    brd = {
        "description": "A simple calculator UI.",
        "requirements": [
            {"id": "R1", "text": "Show digits on a display"},
            {"id": "R2", "text": "Clear button resets to zero"},
        ],
        "forced_architecture": "frontend_only",
    }
    d = detect_architecture(brd, allow_limited_prototype=False).to_dict()
    assert d["blocked"] is False
    assert d["kind"] == "frontend_only"
    assert d["unsupported_requirement_indices"] == []
    print("OK: pure frontend BRD is clean")


if __name__ == "__main__":
    test_block_when_no_limited_prototype()
    test_limited_prototype_marks_unsupported()
    test_pure_frontend_brd_passes_clean()
    print("All HIGH-1 tests passed.")
