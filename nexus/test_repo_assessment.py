"""Focused tests for repository and branch assessment helpers."""

import json

from nexus.repo_assessment import (
    _parse_branches,
    collect_repo_assessment,
    render_repo_assessment,
)


def test_collect_repo_assessment_reports_repo_branch_and_mcp_inventory(
    tmp_path,
):
    (tmp_path / "Aave-V3").mkdir()
    (tmp_path / "Nouns-DAO").mkdir()
    (tmp_path / "Uniswap-V3").mkdir()
    (tmp_path / "contracts").mkdir()
    (tmp_path / "mcp" / "agents").mkdir(parents=True)
    (tmp_path / "docs").mkdir()
    (tmp_path / "contracts" / "NexusGameTheoryToken.sol").write_text(
        "pragma solidity ^0.8.0;"
    )
    (tmp_path / "GOVERNANCE.md").write_text("# Governance")
    (tmp_path / "chimera.html").write_text("<html></html>")
    (tmp_path / "docs" / "guide.md").write_text("# Guide")
    (tmp_path / "mcp" / "agents" / "mig-network-config.json").write_text(
        json.dumps(
            {
                "migNetwork": {
                    "mcpAgents": [{"id": "mcp-001"}, {"id": "mcp-011"}],
                    "mpcServers": [{"id": "mpc-server-001"}],
                }
            }
        )
    )

    def stub_runner(_command):
        return "* main\n  feature/dao\n  remotes/origin/main"

    summary = collect_repo_assessment(
        repo_root=tmp_path, command_runner=stub_runner
    )

    assert summary.current_branch == "main"
    assert [branch.name for branch in summary.branches] == [
        "main",
        "feature/dao",
        "remotes/origin/main",
    ]
    assert summary.web3_protocol_count == 3
    assert summary.custom_mcp_agent_count == 2
    assert summary.custom_mpc_server_count == 1
    assert summary.governance_asset_count == 4
    assert summary.dao_improvement_priorities


def test_render_repo_assessment_mentions_branch_protocols_and_improvements(
    tmp_path,
):
    (tmp_path / "basic-dao").mkdir()
    (tmp_path / "mcp" / "agents").mkdir(parents=True)
    (tmp_path / "mcp" / "agents" / "mig-network-config.json").write_text(
        json.dumps({"migNetwork": {"mcpAgents": [], "mpcServers": []}})
    )

    summary = collect_repo_assessment(
        repo_root=tmp_path,
        command_runner=lambda _command: "* main",
    )

    output = render_repo_assessment(summary)

    assert "REPOSITORY ASSESSMENT" in output
    assert "Current: main" in output
    assert "basic-dao" in output
    assert "[IMPROVE]" in output


# ---------------------------------------------------------------------------
# _parse_branches
# ---------------------------------------------------------------------------

def test_parse_branches_identifies_current_branch():
    raw = "* main\n  feature/dao\n"
    branches = _parse_branches(raw)
    current = [b for b in branches if b.current]
    assert len(current) == 1
    assert current[0].name == "main"


def test_parse_branches_identifies_remote_branches():
    raw = "* main\n  remotes/origin/main\n  origin/feature\n"
    branches = _parse_branches(raw)
    remote = [b for b in branches if b.remote]
    assert len(remote) == 2


def test_parse_branches_non_remote_not_flagged_remote():
    raw = "* main\n  local-branch\n"
    branches = _parse_branches(raw)
    non_remote = [b for b in branches if not b.remote]
    assert any(b.name == "local-branch" for b in non_remote)


def test_parse_branches_empty_string_returns_empty():
    assert _parse_branches("") == []


def test_parse_branches_blank_lines_skipped():
    raw = "\n  \n* main\n\n"
    branches = _parse_branches(raw)
    assert len(branches) == 1
    assert branches[0].name == "main"


# ---------------------------------------------------------------------------
# collect_repo_assessment — non-existent root
# ---------------------------------------------------------------------------

def test_collect_repo_assessment_non_existent_root_warns(tmp_path):
    missing = tmp_path / "does_not_exist"
    summary = collect_repo_assessment(
        repo_root=missing,
        command_runner=lambda _cmd: "",
    )
    assert any("does not exist" in w for w in summary.warnings)
    assert summary.current_branch == "unknown"
    assert summary.branches == []
    assert summary.web3_protocol_count == 0


# ---------------------------------------------------------------------------
# render_repo_assessment — truncation of > 8 protocols
# ---------------------------------------------------------------------------

def test_render_repo_assessment_truncates_protocols_beyond_eight(tmp_path):
    # Create 10 web3 protocol directories
    protocols = [
        "Aave-V3", "Nouns-DAO", "Uniswap-V3", "Uniswap-V2",
        "Uniswap-V4", "Compound", "Synthetix", "GMX.io",
        "ChainLink", "Eigenlayer",
    ]
    for p in protocols:
        (tmp_path / p).mkdir()

    summary = collect_repo_assessment(
        repo_root=tmp_path,
        command_runner=lambda _cmd: "* main",
    )
    output = render_repo_assessment(summary)
    assert "…" in output


# ---------------------------------------------------------------------------
# collect_repo_assessment — git command fails gracefully
# ---------------------------------------------------------------------------

def test_collect_repo_assessment_git_failure_adds_warning(tmp_path):
    import subprocess

    def failing_runner(_cmd):
        raise subprocess.SubprocessError("git not available")

    summary = collect_repo_assessment(
        repo_root=tmp_path,
        command_runner=failing_runner,
    )
    assert any("unavailable" in w for w in summary.warnings)
