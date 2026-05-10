"""Read-only repository and branch assessment helpers."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence

CommandRunner = Callable[[Sequence[str]], str]

WEB3_PROTOCOL_DIRECTORIES = (
    "Aave-V3",
    "ChainLink",
    "Compound",
    "Eigenlayer",
    "Ethereum-Name-Service",
    "GMX.io",
    "Gnosis-Safe",
    "Lens-Protocol",
    "Nouns-DAO",
    "Olympus-DAO",
    "OpenSea-Seaport",
    "PancakeSwap-V3",
    "SuperFluid",
    "SushiSwap-V3",
    "Synthetix",
    "Uniswap-V2",
    "Uniswap-V3",
    "Uniswap-V4",
    "WorldCoin-Core",
    "basic-dao",
    "voting-token",
)

DAO_IMPROVEMENT_RULES = (
    (
        "Increase branch-aware MCP automation so each governance "
        "update is assessed before DAO rollout.",
        lambda summary: len(summary.branches) < 2,
    ),
    (
        "Expand repository-to-web3 benchmarks so treasury, "
        "governance, oracle, and AMM references stay visible "
        "to operators.",
        lambda summary: summary.web3_protocol_count < 10,
    ),
    (
        "Add more DAO execution surfaces to the dashboard so "
        "contributors can trace governance docs, contracts, "
        "and MCP servers together.",
        lambda summary: summary.governance_asset_count < 3,
    ),
)


@dataclass(frozen=True)
class BranchSummary:
    """A normalized git branch reference for UI or CLI reporting."""

    name: str
    remote: bool = False
    current: bool = False


@dataclass(frozen=True)
class RepoAssessmentSummary:
    """Read-only assessment of repository, branch, and DAO surfaces."""

    repo_root: str
    current_branch: str
    branches: List[BranchSummary]
    web3_protocol_count: int
    web3_protocols: List[str]
    solidity_contract_count: int
    documentation_file_count: int
    governance_asset_count: int
    custom_mcp_agent_count: int
    custom_mpc_server_count: int
    dao_improvement_priorities: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def _run_command(command: Sequence[str]) -> str:
    completed = subprocess.run(
        list(command),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _count_files(paths: Iterable[Path], suffixes: Sequence[str]) -> int:
    return sum(
        1
        for path in paths
        if path.is_file()
        and any(path.name.endswith(suffix) for suffix in suffixes)
    )


def _read_mcp_config(repo_root: Path) -> tuple[int, int]:
    config_path = repo_root / "mcp" / "agents" / "mig-network-config.json"
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return 0, 0

    network = data.get("migNetwork", {})
    agents = network.get("mcpAgents", [])
    servers = network.get("mpcServers", [])
    return len(agents), len(servers)


def _parse_branches(raw_output: str) -> List[BranchSummary]:
    branches = []
    for line in raw_output.splitlines():
        name = line.strip()
        if not name:
            continue
        current = name.startswith("* ")
        if current:
            name = name[2:].strip()
        remote = name.startswith("origin/") or name.startswith(
            "remotes/origin/"
        )
        branches.append(
            BranchSummary(name=name, remote=remote, current=current)
        )
    return branches


def _list_branches(
    repo_root: Path,
    command_runner: CommandRunner = _run_command,
) -> tuple[str, List[BranchSummary], List[str]]:
    warnings: List[str] = []
    current_branch = "unknown"
    branches: List[BranchSummary] = []

    try:
        raw_branches = command_runner(
            [
                "git",
                "-C",
                str(repo_root),
                "branch",
                "-a",
                "--no-color",
            ]
        )
        branches = _parse_branches(raw_branches)
    except (OSError, subprocess.SubprocessError) as exc:
        warnings.append(f"Git branch inventory unavailable: {exc}")

    for branch in branches:
        if branch.current:
            current_branch = branch.name
            break

    return current_branch, branches, warnings


def collect_repo_assessment(
    repo_root: Optional[Path] = None,
    command_runner: CommandRunner = _run_command,
) -> RepoAssessmentSummary:
    """Collect a read-only repository assessment for MCP/MPC planning."""

    resolved_root = (repo_root or _default_repo_root()).resolve()
    warnings: List[str] = []

    # Validate the repository root before performing directory operations.
    if not resolved_root.exists():
        warnings.append(f"Repository root does not exist: {resolved_root}")
    elif not resolved_root.is_dir():
        warnings.append(f"Repository root is not a directory: {resolved_root}")

    if warnings:
        # Return an empty assessment with warnings rather than raising.
        summary = RepoAssessmentSummary(
            repo_root=str(resolved_root),
            current_branch="unknown",
            branches=[],
            web3_protocol_count=0,
            web3_protocols=[],
            solidity_contract_count=0,
            documentation_file_count=0,
            governance_asset_count=0,
            custom_mcp_agent_count=0,
            custom_mpc_server_count=0,
            warnings=warnings,
        )

        priorities = [
            message
            for message, predicate in DAO_IMPROVEMENT_RULES
            if predicate(summary)
        ]
        if not priorities:
            priorities.append(
                "Maintain the current MCP/MPC coverage by reviewing "
                "repository branches, governance artifacts, and "
                "web3 protocol references together."
            )

        return replace(
            summary,
            dao_improvement_priorities=priorities,
        )

    top_level_paths = list(resolved_root.iterdir())
    web3_protocols = sorted(
        path.name
        for path in top_level_paths
        if path.is_dir() and path.name in WEB3_PROTOCOL_DIRECTORIES
    )
    solidity_contract_count = _count_files(
        resolved_root.rglob("*.sol"),
        (".sol",),
    )
    documentation_file_count = _count_files(
        resolved_root.rglob("*"),
        (".md", ".html"),
    )
    governance_assets = [
        resolved_root / "GOVERNANCE.md",
        resolved_root / "contracts" / "NexusGameTheoryToken.sol",
        resolved_root / "mcp" / "agents" / "mig-network-config.json",
        resolved_root / "chimera.html",
    ]
    governance_asset_count = sum(path.exists() for path in governance_assets)
    custom_mcp_agent_count, custom_mpc_server_count = _read_mcp_config(
        resolved_root
    )
    current_branch, branches, branch_warnings = _list_branches(
        resolved_root, command_runner=command_runner
    )
    warnings.extend(branch_warnings)

    summary = RepoAssessmentSummary(
        repo_root=str(resolved_root),
        current_branch=current_branch,
        branches=branches,
        web3_protocol_count=len(web3_protocols),
        web3_protocols=web3_protocols,
        solidity_contract_count=solidity_contract_count,
        documentation_file_count=documentation_file_count,
        governance_asset_count=governance_asset_count,
        custom_mcp_agent_count=custom_mcp_agent_count,
        custom_mpc_server_count=custom_mpc_server_count,
        warnings=warnings,
    )

    priorities = [
        message
        for message, predicate in DAO_IMPROVEMENT_RULES
        if predicate(summary)
    ]
    if not priorities:
        priorities.append(
            "Maintain the current MCP/MPC coverage by reviewing "
            "repository branches, governance artifacts, and "
            "web3 protocol references together."
        )

    return replace(
        summary,
        dao_improvement_priorities=priorities,
    )


def render_repo_assessment(summary: RepoAssessmentSummary) -> str:
    """Render a concise CLI summary of repository/branch/DAO coverage."""

    branch_names = (
        ", ".join(branch.name for branch in summary.branches) or "none"
    )
    protocol_names = ", ".join(summary.web3_protocols[:8])
    if len(summary.web3_protocols) > 8:
        protocol_names = f"{protocol_names}, …"
    protocol_names = protocol_names or "none"

    lines = [
        "[NEXUS MCP/MPC REPOSITORY ASSESSMENT]",
        f"[ROOT] {summary.repo_root}",
        "[BRANCH] "
        f"Current: {summary.current_branch} | Inventory: {branch_names}",
        "[WEB3] "
        f"{summary.web3_protocol_count} protocol directories | "
        f"Top matches: {protocol_names}",
        "[DAO] "
        f"Governance assets: {summary.governance_asset_count} | "
        f"Solidity contracts: {summary.solidity_contract_count}",
        "[MCP] "
        f"Agents: {summary.custom_mcp_agent_count} | "
        f"MPC servers: {summary.custom_mpc_server_count}",
    ]
    for priority in summary.dao_improvement_priorities:
        lines.append(f"[IMPROVE] {priority}")
    for warning in summary.warnings:
        lines.append(f"[WARN] {warning}")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point for repository assessment."""

    parser = argparse.ArgumentParser(
        description="Read-only Nexus repository assessment"
    )
    parser.add_argument(
        "--repo-root",
        default="",
        help="Optional repository root to assess.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of the human-readable summary.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve() if args.repo_root else None
    summary = collect_repo_assessment(repo_root=repo_root)

    if args.json:
        print(json.dumps(asdict(summary), indent=2))
    else:
        print(render_repo_assessment(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
