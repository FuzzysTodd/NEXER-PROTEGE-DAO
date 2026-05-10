"""Unit tests for the finance_ops_report Python logic."""

from __future__ import annotations

import json

from nexus.finance_ops_report import (
    Finding,
    collect_agent_findings,
    collect_filename_findings,
    collect_json_findings,
    collect_python_findings,
    is_first_party_preerror_path,
    iter_repo_files,
    read_text,
    scan_keywords,
    scan_risk_patterns,
)


# ---------------------------------------------------------------------------
# Finding
# ---------------------------------------------------------------------------

def test_finding_as_dict_returns_all_keys():
    f = Finding(
        severity="high",
        category="python-syntax",
        file="nexus/foo.py",
        message="Syntax error at line 3: invalid syntax",
    )
    d = f.as_dict()
    assert d["severity"] == "high"
    assert d["category"] == "python-syntax"
    assert d["file"] == "nexus/foo.py"
    assert "Syntax error" in d["message"]


# ---------------------------------------------------------------------------
# is_first_party_preerror_path
# ---------------------------------------------------------------------------

def test_is_first_party_for_top_level_file(tmp_path):
    p = tmp_path / "README.md"
    p.touch()
    assert is_first_party_preerror_path(tmp_path, p) is True


def test_is_first_party_for_nexus_subdirectory(tmp_path):
    sub = tmp_path / "nexus" / "module.py"
    sub.parent.mkdir()
    sub.touch()
    assert is_first_party_preerror_path(tmp_path, sub) is True


def test_is_first_party_for_docs_subdirectory(tmp_path):
    sub = tmp_path / "docs" / "guide.md"
    sub.parent.mkdir()
    sub.touch()
    assert is_first_party_preerror_path(tmp_path, sub) is True


def test_is_not_first_party_for_external_directory(tmp_path):
    sub = tmp_path / "Uniswap-V3" / "pool.sol"
    sub.parent.mkdir()
    sub.touch()
    assert is_first_party_preerror_path(tmp_path, sub) is False


# ---------------------------------------------------------------------------
# iter_repo_files
# ---------------------------------------------------------------------------

def test_iter_repo_files_yields_text_files(tmp_path):
    (tmp_path / "nexus").mkdir()
    (tmp_path / "nexus" / "module.py").write_text("x = 1")
    (tmp_path / "nexus" / "data.bin").write_bytes(b"\x00\x01")
    paths = list(iter_repo_files(tmp_path))
    names = [p.name for p in paths]
    assert "module.py" in names
    assert "data.bin" not in names


def test_iter_repo_files_excludes_pycache(tmp_path):
    cache = tmp_path / "__pycache__"
    cache.mkdir()
    (cache / "module.pyc").write_bytes(b"\x00")
    (tmp_path / "real.py").write_text("pass")
    paths = list(iter_repo_files(tmp_path))
    names = [p.name for p in paths]
    assert "module.pyc" not in names
    assert "real.py" in names


def test_iter_repo_files_excludes_node_modules(tmp_path):
    nm = tmp_path / "node_modules"
    nm.mkdir()
    (nm / "lib.js").write_text("var x = 1;")
    (tmp_path / "app.js").write_text("var y = 2;")
    paths = list(iter_repo_files(tmp_path))
    names = [p.name for p in paths]
    assert "lib.js" not in names
    assert "app.js" in names


# ---------------------------------------------------------------------------
# read_text
# ---------------------------------------------------------------------------

def test_read_text_returns_content(tmp_path):
    p = tmp_path / "hello.txt"
    p.write_text("hello world", encoding="utf-8")
    assert read_text(p) == "hello world"


def test_read_text_returns_none_for_missing_file(tmp_path):
    p = tmp_path / "nonexistent.txt"
    assert read_text(p) is None


# ---------------------------------------------------------------------------
# collect_python_findings
# ---------------------------------------------------------------------------

def test_collect_python_findings_clean_file_no_findings(tmp_path):
    (tmp_path / "nexus").mkdir()
    (tmp_path / "nexus" / "ok.py").write_text("x = 1\ny = 2\n")
    findings = collect_python_findings(tmp_path)
    assert all(f.file != "nexus/ok.py" for f in findings)


def test_collect_python_findings_syntax_error_flagged(tmp_path):
    (tmp_path / "nexus").mkdir()
    (tmp_path / "nexus" / "bad.py").write_text("def broken(\n")
    findings = collect_python_findings(tmp_path)
    assert any("bad.py" in f.file for f in findings)
    assert all(f.severity == "high" for f in findings if "bad.py" in f.file)
    assert all(f.category == "python-syntax" for f in findings if "bad.py" in f.file)


def test_collect_python_findings_only_first_party(tmp_path):
    """Files outside first-party roots must not be flagged."""
    ext = tmp_path / "Uniswap-V3"
    ext.mkdir()
    (ext / "broken.py").write_text("def broken(\n")
    findings = collect_python_findings(tmp_path)
    assert all("Uniswap-V3" not in f.file for f in findings)


# ---------------------------------------------------------------------------
# collect_json_findings
# ---------------------------------------------------------------------------

def test_collect_json_findings_valid_json_no_findings(tmp_path):
    (tmp_path / "valid.json").write_text(json.dumps({"key": "value"}))
    findings = collect_json_findings(tmp_path)
    assert all("valid.json" not in f.file for f in findings)


def test_collect_json_findings_invalid_top_level_json_flagged(tmp_path):
    (tmp_path / "broken.json").write_text("{invalid json")
    findings = collect_json_findings(tmp_path)
    assert any("broken.json" in f.file for f in findings)
    for f in findings:
        if "broken.json" in f.file:
            assert f.category == "json-parse"
            assert f.severity == "medium"


def test_collect_json_findings_invalid_in_nexus_subdir(tmp_path):
    (tmp_path / "nexus").mkdir()
    (tmp_path / "nexus" / "bad.json").write_text("{bad}")
    findings = collect_json_findings(tmp_path)
    assert any("bad.json" in f.file for f in findings)


# ---------------------------------------------------------------------------
# collect_agent_findings
# ---------------------------------------------------------------------------

def test_collect_agent_findings_no_agents_dir_returns_empty(tmp_path):
    findings = collect_agent_findings(tmp_path)
    assert findings == []


def test_collect_agent_findings_valid_agent_no_findings(tmp_path):
    agents_dir = tmp_path / ".github" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "my-agent.agent.md").write_text(
        "---\nname: my-agent\ndescription: does stuff\n---\n# Body\n"
    )
    findings = collect_agent_findings(tmp_path)
    assert findings == []


def test_collect_agent_findings_missing_frontmatter_flagged(tmp_path):
    agents_dir = tmp_path / ".github" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "nofrontmatter.agent.md").write_text("# Just a heading\n")
    findings = collect_agent_findings(tmp_path)
    assert any("nofrontmatter.agent.md" in f.file for f in findings)
    for f in findings:
        if "nofrontmatter.agent.md" in f.file:
            assert f.category == "agent-frontmatter"


def test_collect_agent_findings_missing_name_field_flagged(tmp_path):
    agents_dir = tmp_path / ".github" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "nodesc.agent.md").write_text(
        "---\ndescription: something\n---\n# Body\n"
    )
    findings = collect_agent_findings(tmp_path)
    assert any("nodesc.agent.md" in f.file for f in findings)


# ---------------------------------------------------------------------------
# collect_filename_findings
# ---------------------------------------------------------------------------

def test_collect_filename_findings_copy_pattern_flagged(tmp_path):
    (tmp_path / "contract(copy).sol").write_text("pragma solidity ^0.8.0;")
    findings = collect_filename_findings(tmp_path)
    assert any("(copy)" in f.file for f in findings)
    for f in findings:
        if "(copy)" in f.file:
            assert f.category == "naming-drift"
            assert f.severity == "low"


def test_collect_filename_findings_normal_file_not_flagged(tmp_path):
    (tmp_path / "normal.sol").write_text("pragma solidity ^0.8.0;")
    findings = collect_filename_findings(tmp_path)
    assert all("normal.sol" not in f.file for f in findings)


# ---------------------------------------------------------------------------
# scan_keywords
# ---------------------------------------------------------------------------

def test_scan_keywords_withdraw_detects_matches(tmp_path):
    (tmp_path / "ops").mkdir()
    (tmp_path / "ops" / "payment.sol").write_text("function withdraw() { claim(); }")
    results = scan_keywords(tmp_path, "withdraw")
    assert any(r["count"] > 0 for r in results)


def test_scan_keywords_placement_detects_treasury(tmp_path):
    (tmp_path / "nexus").mkdir()
    (tmp_path / "nexus" / "finance.py").write_text("treasury = 100; yield_amount = 5")
    results = scan_keywords(tmp_path, "placement")
    assert any(r["count"] > 0 for r in results)


def test_scan_keywords_empty_repo_returns_empty(tmp_path):
    results = scan_keywords(tmp_path, "withdraw")
    assert results == []


def test_scan_keywords_results_sorted_by_count_desc(tmp_path):
    (tmp_path / "a.sol").write_text("withdraw withdraw withdraw")
    (tmp_path / "b.sol").write_text("withdraw")
    results = scan_keywords(tmp_path, "withdraw")
    if len(results) >= 2:
        assert results[0]["count"] >= results[1]["count"]


# ---------------------------------------------------------------------------
# scan_risk_patterns
# ---------------------------------------------------------------------------

def test_scan_risk_patterns_detects_delegatecall(tmp_path):
    (tmp_path / "hack.sol").write_text("target.delegatecall(data);")
    results = scan_risk_patterns(tmp_path)
    names = [r["pattern"] for r in results]
    assert "delegatecall" in names


def test_scan_risk_patterns_detects_tx_origin(tmp_path):
    (tmp_path / "auth.sol").write_text("require(tx.origin == owner);")
    results = scan_risk_patterns(tmp_path)
    names = [r["pattern"] for r in results]
    assert "tx.origin" in names


def test_scan_risk_patterns_empty_repo_returns_empty(tmp_path):
    results = scan_risk_patterns(tmp_path)
    assert results == []


def test_scan_risk_patterns_selfdestruct_detected(tmp_path):
    (tmp_path / "bomb.sol").write_text("selfdestruct(payable(owner));")
    results = scan_risk_patterns(tmp_path)
    names = [r["pattern"] for r in results]
    assert "selfdestruct" in names
