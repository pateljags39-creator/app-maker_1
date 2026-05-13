"""Acceptance engine: real checks, never silent passes.

Returns honest PASS/PARTIAL/FAIL per check + an overall verdict.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CheckResult:
    name: str
    status: str  # PASS | PARTIAL | FAIL
    detail: str = ""
    severity: str = "info"  # info | warning | error


@dataclass
class AcceptanceReport:
    overall: str  # PASS | PARTIAL | FAIL
    checks: list[CheckResult] = field(default_factory=list)
    requirement_coverage: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall": self.overall,
            "checks": [asdict(c) for c in self.checks],
            "requirement_coverage": self.requirement_coverage,
        }


SECRET_REGEXES = [
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]


def _walk_text_files(root: Path, suffixes=(".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".html", ".css", ".md", ".env", ".yaml", ".yml")):
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if set(rel.parts) & {"node_modules", ".factory", ".git", "dist", "build", "__pycache__"}:
            continue
        if p.suffix.lower() not in suffixes:
            continue
        yield p


def run_acceptance(
    workspace: Path,
    brd: dict[str, Any],
    architecture: dict[str, Any],
    build_summary: dict[str, Any] | None = None,
) -> AcceptanceReport:
    workspace = Path(workspace)
    report = AcceptanceReport(overall="PASS")

    # 1) Architecture fit -- does the workspace contain the directories the architecture expects?
    if architecture.get("requires_backend") and not (workspace / "backend").exists():
        report.checks.append(CheckResult("architecture.backend_dir", "FAIL", "backend/ missing but required", "error"))
    else:
        report.checks.append(CheckResult("architecture.backend_dir", "PASS", "backend/ present or not required"))
    if architecture.get("kind") != "backend_required" and not (workspace / "frontend").exists():
        report.checks.append(CheckResult("architecture.frontend_dir", "FAIL", "frontend/ missing", "error"))
    else:
        report.checks.append(CheckResult("architecture.frontend_dir", "PASS", "frontend/ present or not required"))

    # 2) Frontend essentials
    fe = workspace / "frontend"
    if fe.exists():
        for f in ("package.json", "vite.config.js", "index.html", "src/main.jsx", "src/App.jsx"):
            ok = (fe / f).exists()
            report.checks.append(CheckResult(
                f"frontend.has.{f.replace('/', '_')}",
                "PASS" if ok else "FAIL",
                f"{f} {'found' if ok else 'missing'}",
                "info" if ok else "error",
            ))
        # Confirm React+Vite stack
        pj = fe / "package.json"
        if pj.exists():
            try:
                data = json.loads(pj.read_text())
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                if "vite" in deps and "react" in deps:
                    report.checks.append(CheckResult("frontend.stack", "PASS", "React+Vite declared"))
                else:
                    report.checks.append(CheckResult("frontend.stack", "FAIL", f"package.json deps: {list(deps)[:10]}", "error"))
            except Exception as e:
                report.checks.append(CheckResult("frontend.stack", "FAIL", f"package.json invalid: {e}", "error"))

    # 3) Backend essentials
    be = workspace / "backend"
    if be.exists():
        for f in ("main.py", "requirements.txt"):
            ok = (be / f).exists()
            report.checks.append(CheckResult(
                f"backend.has.{f}",
                "PASS" if ok else "FAIL",
                f"{f} {'found' if ok else 'missing'}",
                "info" if ok else "error",
            ))
        req = be / "requirements.txt"
        if req.exists():
            txt = req.read_text().lower()
            if "fastapi" in txt:
                report.checks.append(CheckResult("backend.stack", "PASS", "FastAPI declared"))
            else:
                report.checks.append(CheckResult("backend.stack", "FAIL", "FastAPI not in requirements", "error"))
        main = be / "main.py"
        if main.exists():
            mt = main.read_text("utf-8", "replace")
            if re.search(r"FastAPI\s*\(", mt) and re.search(r"/api", mt):
                report.checks.append(CheckResult("backend.api_prefix", "PASS", "FastAPI app + /api prefix"))
            else:
                report.checks.append(CheckResult("backend.api_prefix", "PARTIAL", "missing FastAPI init or /api prefix", "warning"))

    # 4) Secret hygiene
    secret_hits = []
    for p in _walk_text_files(workspace):
        try:
            text = p.read_text("utf-8", "replace")
        except Exception:
            continue
        for rx in SECRET_REGEXES:
            for m in rx.finditer(text):
                secret_hits.append({"file": str(p.relative_to(workspace)), "hit": m.group(0)[:8] + "***"})
    if secret_hits:
        report.checks.append(CheckResult("secrets.scan", "FAIL", f"{len(secret_hits)} secret-like tokens found in generated files", "error"))
    else:
        report.checks.append(CheckResult("secrets.scan", "PASS", "no secret-like tokens detected"))

    # 5) Build summary integration
    if build_summary is not None:
        status = build_summary.get("overall_status", "FAIL")
        report.checks.append(CheckResult(
            "build.overall",
            status,
            f"build overall_status={status}; duration={build_summary.get('summary', {}).get('duration_s')}s",
            "info" if status == "PASS" else ("warning" if status == "PARTIAL" else "error"),
        ))

    # 6.5) Auto-stubs honesty check
    stub_marker = workspace / ".factory" / "stubs.json"
    if stub_marker.exists():
        try:
            import json as _json
            data = _json.loads(stub_marker.read_text(encoding="utf-8"))
            stubs = data.get("stubs", []) or []
        except Exception:
            stubs = []
        if stubs:
            ellipsis = "\u2026" if len(stubs) > 5 else ""
            stub_list = ", ".join(stubs[:5])
            report.checks.append(CheckResult(
                "generation.auto_stubs",
                "PARTIAL",
                (
                    f"{len(stubs)} module(s) were auto-stubbed because the LLM "
                    f"referenced them via import but did not generate them: "
                    f"{stub_list}{ellipsis}. "
                    "Build passes but those parts are placeholders."
                ),
                "warning",
            ))

    # 7) Requirement coverage (simple keyword mapping)
    coverage: list[dict[str, Any]] = []
    requirements = brd.get("requirements", []) or []
    workspace_files: list[Path] = [p for p in workspace.rglob("*") if p.is_file()]
    workspace_text: dict[str, str] = {}
    for p in workspace_files:
        if set(p.relative_to(workspace).parts) & {"node_modules", ".factory", ".git", "dist", "build", "__pycache__"}:
            continue
        try:
            workspace_text[str(p.relative_to(workspace))] = p.read_text("utf-8", "replace")
        except Exception:
            continue

    for req in requirements:
        text = (req.get("text", "") if isinstance(req, dict) else str(req)).strip()
        if not text:
            continue
        # HIGH-1: honor explicitly-unsupported requirements (frontend_only limited_prototype
        # path) — record them as honestly unsupported, not as weak coverage.
        req_status = req.get("status") if isinstance(req, dict) else None
        if req_status == "unsupported":
            coverage.append({
                "requirement": text,
                "matched_files": [],
                "status": "UNSUPPORTED",
                "reason": (req.get("unsupported_reason") if isinstance(req, dict) else None) or "marked unsupported in BRD",
            })
            continue
        keys = [k for k in re.findall(r"\b\w{4,}\b", text.lower()) if k not in {"with", "this", "that", "have", "from", "will", "each", "into", "shall", "must"}]
        matched: list[str] = []
        for path, content in workspace_text.items():
            lc = content.lower()
            if any(k in lc for k in keys[:6]):
                matched.append(path)
            if len(matched) >= 5:
                break
        coverage.append({
            "requirement": text,
            "matched_files": matched,
            "status": "PASS" if matched else "PARTIAL",
        })
    report.requirement_coverage = coverage
    # Exclude UNSUPPORTED from coverage gap math; surface them as their own info check.
    unsupported_count = sum(1 for c in coverage if c["status"] == "UNSUPPORTED")
    coverable = [c for c in coverage if c["status"] != "UNSUPPORTED"]
    if unsupported_count:
        report.checks.append(CheckResult(
            "requirements.unsupported_acknowledged",
            "PARTIAL",
            f"{unsupported_count} requirement(s) explicitly marked unsupported (limited_prototype / architecture gate).",
            "warning",
        ))
    if coverable and all(c["status"] == "PASS" for c in coverable):
        report.checks.append(CheckResult("requirements.coverage", "PASS", f"{len(coverable)} requirements matched"))
    elif coverable:
        partials = sum(1 for c in coverable if c["status"] != "PASS")
        report.checks.append(CheckResult("requirements.coverage", "PARTIAL", f"{partials}/{len(coverable)} requirements have weak coverage", "warning"))
    elif not unsupported_count:
        report.checks.append(CheckResult("requirements.coverage", "PARTIAL", "no structured requirements provided", "warning"))

    # Overall
    statuses = [c.status for c in report.checks]
    if any(s == "FAIL" for s in statuses):
        report.overall = "FAIL"
    elif any(s == "PARTIAL" for s in statuses):
        report.overall = "PARTIAL"
    else:
        report.overall = "PASS"
    return report
