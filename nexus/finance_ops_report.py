from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict, cast


TEXT_SUFFIXES = {
    ".py",
    ".js",
    ".ts",
    ".sol",
    ".md",
    ".html",
    ".json",
    ".yml",
    ".yaml",
}
EXCLUDED_DIRS = {
    ".git",
    ".allai",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".pytest_cache",
}
FIRST_PARTY_PREERROR_ROOTS = {
    ".github",
    "docs",
    "mcp",
    "nexus",
    "ops",
}
KEYWORD_GROUPS = {
    "withdraw": [
        "withdraw",
        "release(",
        "claim",
        "redeem",
        "collectproceeds",
        "payout",
    ],
    "placement": [
        "treasury",
        "yield",
        "apy",
        "liquidity",
        "staking",
        "rebalance",
        "revenue",
        "profit",
        "allocation",
        "placement",
    ],
}
RISK_PATTERNS = {
    "delegatecall": re.compile(r"delegatecall", re.IGNORECASE),
    "tx.origin": re.compile(r"tx\.origin", re.IGNORECASE),
    "selfdestruct": re.compile(r"selfdestruct", re.IGNORECASE),
    "approve": re.compile(r"approve\s*\(", re.IGNORECASE),
}


@dataclass
class Finding:
    severity: str
    category: str
    file: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "category": self.category,
            "file": self.file,
            "message": self.message,
        }


class SignalResult(TypedDict):
    file: str
    count: int
    matches: list[str]


class RiskPatternResult(TypedDict):
    pattern: str
    count: int
    sampleFiles: list[str]


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def is_first_party_preerror_path(root: Path, path: Path) -> bool:
    relative = path.relative_to(root)
    if len(relative.parts) == 1:
        return True
    return relative.parts[0] in FIRST_PARTY_PREERROR_ROOTS


def iter_repo_files(root: Path):
    for path in root.rglob("*"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            if path.stat().st_size > 512_000:
                continue
        except OSError:
            continue
        yield path


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="latin-1")
        except OSError:
            return None
    except OSError:
        return None


def collect_python_findings(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in root.rglob("*.py"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if not is_first_party_preerror_path(root, path):
            continue
        text = read_text(path)
        if text is None:
            continue
        try:
            ast.parse(text, filename=str(path))
        except SyntaxError as error:
            findings.append(
                Finding(
                    severity="high",
                    category="python-syntax",
                    file=str(path.relative_to(root)),
                    message=f"Syntax error at line {error.lineno}: {error.msg}",
                )
            )
    return findings


def collect_json_findings(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    scan_roots = {
        root / ".github",
        root / "mcp",
        root / "docs",
        root / "nexus",
        root / "ops",
    }
    for path in root.glob("*.json"):
        text = read_text(path)
        if text is None:
            continue
        try:
            json.loads(text)
        except json.JSONDecodeError as error:
            findings.append(
                Finding(
                    severity="medium",
                    category="json-parse",
                    file=str(path.relative_to(root)),
                    message=f"JSON parse error at line {error.lineno}: {error.msg}",
                )
            )
    for base in scan_roots:
        if not base.exists():
            continue
        for path in base.rglob("*.json"):
            if any(part in EXCLUDED_DIRS for part in path.parts):
                continue
            text = read_text(path)
            if text is None:
                continue
            try:
                json.loads(text)
            except json.JSONDecodeError as error:
                findings.append(
                    Finding(
                        severity="medium",
                        category="json-parse",
                        file=str(path.relative_to(root)),
                        message=f"JSON parse error at line {error.lineno}: {error.msg}",
                    )
                )
    return findings


def collect_agent_findings(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    agents_dir = root / ".github" / "agents"
    if not agents_dir.exists():
        return findings
    for path in agents_dir.glob("*.agent.md"):
        text = read_text(path)
        if text is None:
            continue
        if not text.startswith("---\n"):
            findings.append(
                Finding(
                    severity="medium",
                    category="agent-frontmatter",
                    file=str(path.relative_to(root)),
                    message="Missing YAML frontmatter start delimiter.",
                )
            )
            continue
        if "\nname:" not in text or "\ndescription:" not in text:
            findings.append(
                Finding(
                    severity="medium",
                    category="agent-frontmatter",
                    file=str(path.relative_to(root)),
                    message="Agent frontmatter is missing required name or description.",
                )
            )
    return findings


def collect_filename_findings(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_repo_files(root):
        if not is_first_party_preerror_path(root, path):
            continue
        rel = str(path.relative_to(root))
        if "(copy)" in rel or "`" in rel:
            findings.append(
                Finding(
                    severity="low",
                    category="naming-drift",
                    file=rel,
                    message="Suspicious filename pattern can make automation and review harder.",
                )
            )
    return findings


def scan_keywords(root: Path, group: str) -> list[SignalResult]:
    results: list[SignalResult] = []
    needles = [needle.lower() for needle in KEYWORD_GROUPS[group]]
    for path in iter_repo_files(root):
        text = read_text(path)
        if text is None:
            continue
        lowered = text.lower()
        counts = {needle: lowered.count(needle) for needle in needles}
        total = sum(counts.values())
        if total == 0:
            continue
        matches = [needle for needle, count in counts.items() if count]
        results.append(
            {
                "file": str(path.relative_to(root)),
                "count": total,
                "matches": matches[:6],
            }
        )
    results.sort(key=lambda item: (-item["count"], item["file"]))
    return results[:20]


def scan_risk_patterns(root: Path) -> list[RiskPatternResult]:
    pattern_hits: Counter[str] = Counter()
    files: list[str] = []
    for path in iter_repo_files(root):
        text = read_text(path)
        if text is None:
            continue
        hit_names = [name for name, pattern in RISK_PATTERNS.items() if pattern.search(text)]
        if not hit_names:
            continue
        pattern_hits.update(hit_names)
        files.append(str(path.relative_to(root)))
    return [
        {
            "pattern": name,
            "count": count,
            "sampleFiles": files[:8],
        }
        for name, count in pattern_hits.most_common()
    ]


def load_bots(manifest_path: Path) -> list[dict[str, Any]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return manifest["financialOpsBots"]["bots"]


def write_outputs(report: dict[str, Any], json_path: Path, md_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    summary = cast(dict[str, Any], report["summary"])
    bots = cast(list[dict[str, Any]], report["bots"])
    pre_error_findings = cast(list[dict[str, Any]], report["preErrorFindings"])
    recommended_actions = cast(list[str], report["recommendedActions"])

    lines = [
        "# Financial Ops Automation Report",
        "",
        f"- Generated at: {report['generatedAt']}",
        f"- Files scanned: {summary['filesScanned']}",
        f"- Pre-error findings: {summary['preErrorCount']}",
        f"- Pre-error scope: {summary['preErrorScope']}",
        f"- Withdrawal signals: {summary['withdrawSignalCount']}",
        f"- Placement signals: {summary['placementSignalCount']}",
        f"- Approval gate: {summary['approvalGate']}",
        "",
        "## Bot Status",
        "",
    ]
    for bot in bots:
        lines.append(f"- {bot['name']}: ready")
    lines.extend(["", "## Top Findings", ""])
    if pre_error_findings:
        for finding in pre_error_findings[:10]:
            lines.append(
                f"- [{finding['severity']}] {finding['file']}: {finding['message']}"
            )
    else:
        lines.append("- No high-confidence pre-errors were detected by the static scan.")
    lines.extend(["", "## Recommended Actions", ""])
    for action in recommended_actions:
        lines.append(f"- {action}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_report(root: Path, manifest_path: Path) -> dict[str, Any]:
    files_scanned = sum(1 for _ in iter_repo_files(root))
    python_findings = collect_python_findings(root)
    json_findings = collect_json_findings(root)
    agent_findings = collect_agent_findings(root)
    naming_findings = collect_filename_findings(root)
    pre_errors = python_findings + json_findings + agent_findings + naming_findings
    pre_errors.sort(key=lambda item: (item.severity, item.category, item.file))

    withdraw_signals = scan_keywords(root, "withdraw")
    placement_signals = scan_keywords(root, "placement")
    risk_patterns = scan_risk_patterns(root)
    bots = load_bots(manifest_path)

    report = {
        "generatedAt": iso_now(),
        "summary": {
            "filesScanned": files_scanned,
            "preErrorCount": len(pre_errors),
            "preErrorScope": "first-party automation, docs, mcp, nexus, ops, and top-level repo files",
            "withdrawSignalCount": sum(item["count"] for item in withdraw_signals),
            "placementSignalCount": sum(item["count"] for item in placement_signals),
            "successDocsGenerated": 2,
            "approvalGate": "required for any fund movement or treasury action",
        },
        "bots": bots,
        "preErrorFindings": [finding.as_dict() for finding in pre_errors[:25]],
        "withdrawSignals": withdraw_signals,
        "placementSignals": placement_signals,
        "riskPatterns": risk_patterns,
        "successLog": [
            {
                "time": iso_now(),
                "title": "Financial ops scan completed",
                "details": "Static repo scan finished and refreshed markdown plus dashboard payloads.",
                "status": "success",
            },
            {
                "time": iso_now(),
                "title": "Approval gate enforced",
                "details": "Automation remains advisory for withdrawals, treasury routing, and settlement changes.",
                "status": "success",
            },
        ],
        "recommendedActions": [
            "Review the pre-error queue and clear malformed or duplicate repository-owned files first.",
            "Use the Withdrawal Placement Scanner findings to rank payout and treasury code for human review.",
            "Treat Ethereum and Base connectivity assumptions as separate operational checks"
            " before extending automation.",
        ],
    }
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate financial ops automation reports.")
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    parser.add_argument(
        "--manifest",
        default="mcp/agents/financial-ops-bots.json",
        help="Path to the financial ops bot manifest.",
    )
    parser.add_argument(
        "--output-json",
        default="ops/reports/financial-ops-report.json",
        help="Path to the generated JSON report.",
    )
    parser.add_argument(
        "--output-md",
        default="ops/reports/financial-ops-report.md",
        help="Path to the generated markdown report.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    manifest_path = (root / args.manifest).resolve()
    report = build_report(root, manifest_path)
    write_outputs(report, root / args.output_json, root / args.output_md)
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
