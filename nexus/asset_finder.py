"""Token and contract asset finder for the Nexus Protocol repository.

Scans all Solidity (.sol) files in the repository and classifies each
token contract by standard (ERC-20, ERC-721, ERC-1155, governance, other),
then separates first-party Nexus-authored contracts from third-party
protocol library copies.

Usage (CLI)::

    python -m nexus.asset_finder

Usage (programmatic)::

    from nexus.asset_finder import find_token_assets, render_asset_report
    inventory = find_token_assets()
    print(render_asset_report(inventory))
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# ---------------------------------------------------------------------------
# First-party (owner-authored) top-level directories
# ---------------------------------------------------------------------------

#: Top-level directory names that contain owner-authored token/NFT projects.
OWNER_TOKEN_DIRECTORIES: tuple[str, ...] = (
    "contracts",
    "mintable-token",
    "burnable-token",
    "voting-token",
    "dividend-paying-token-with-buy-sell-fee",
    "reflection-token-supporting-3-wallets",
    "Buyback-Token-with-Fees",
    "erc20-token-with-automatic-vesting",
    "tether-usdt",
    "AntiBot-ERC20",
    "flagship-cookbook-nft",
    "simple-nft-sale",
    "multi-collection-nft-with-burnable-nfts-and-pausable-transfers",
    "soulbound-nft",
    "nft-staking-with-infinite-rewards",
    "on-chain-income-splitter-and-distributor",
    "royalty-splitter",
    "ERC20-NFT-Sale-with-Distributed-Royalties",
    "ERC20-NFT-Sale-with-Distributed-Royalties(copy)",
    "ERC20-NFT-Sale-with-Distributed-Royalties(copy)(copy)",
    "soulbound-nft(copy)",
    "multi-collection-nft-with-burnable-nfts-and-pausable-transfers(copy)",
)

#: Path segments that indicate a vendored/bundled library copy rather than
#: an owner-authored file.  Any file whose path contains one of these
#: segments is treated as a third-party library contract.
LIBRARY_PATH_SEGMENTS: tuple[str, ...] = (
    "@openzeppelin",
    "@rari-capital",
    "openzeppelin-solidity",
    "openzeppelin-contracts",
    "lib/",
    "node_modules",
)

# ---------------------------------------------------------------------------
# Contract classification patterns
# ---------------------------------------------------------------------------

#: Compiled regex for extracting the primary contract name from a Solidity
#: source file.  Matches ``contract Name`` or ``abstract contract Name``.
_CONTRACT_NAME_RE = re.compile(
    r"^\s*(?:abstract\s+)?contract\s+(\w+)",
    re.MULTILINE,
)

#: Mapping from token standard label to the inheritance patterns that
#: identify it.  Patterns are matched case-sensitively against the
#: ``is ...`` clause of each contract declaration.
_STANDARD_PATTERNS: dict[str, re.Pattern[str]] = {
    "ERC-1155": re.compile(r"\bERC1155\b"),
    "ERC-721": re.compile(r"\bERC721\b"),
    "ERC-20": re.compile(r"\bERC20\b|\bIERC20\b"),
    "Governance": re.compile(
        r"\b(?:ERC20Votes|GovernorVotes|IGovernor|Governor)\b"
    ),
}

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TokenAsset:
    """A single Solidity contract identified as a token or NFT asset.

    Attributes
    ----------
    relative_path:
        File path relative to the repository root.
    contract_name:
        Primary ``contract`` name extracted from the source file.
    token_standards:
        Ordered list of token standards detected (e.g. ``["ERC-20"]``).
    is_owner_contract:
        ``True`` when the file lives in a first-party project directory
        and is not a vendored library copy.
    top_directory:
        The top-level directory of the repository that contains this file.
    """

    relative_path: str
    contract_name: str
    token_standards: List[str] = field(default_factory=list)
    is_owner_contract: bool = False
    top_directory: str = ""


@dataclass(frozen=True)
class TokenAssetInventory:
    """Complete token/NFT asset inventory for the repository.

    Attributes
    ----------
    repo_root:
        Absolute path to the repository root that was scanned.
    owner_contracts:
        First-party Nexus-authored token/NFT contracts.
    protocol_contracts:
        Third-party protocol token contracts (Uniswap, Compound, …).
    total_solidity_files_scanned:
        Total number of ``.sol`` files examined during the scan.
    erc20_count:
        Number of ERC-20 contracts (owner + protocol combined).
    erc721_count:
        Number of ERC-721 contracts (owner + protocol combined).
    erc1155_count:
        Number of ERC-1155 contracts (owner + protocol combined).
    governance_count:
        Number of governance/voting token contracts.
    """

    repo_root: str
    owner_contracts: List[TokenAsset] = field(default_factory=list)
    protocol_contracts: List[TokenAsset] = field(default_factory=list)
    total_solidity_files_scanned: int = 0
    erc20_count: int = 0
    erc721_count: int = 0
    erc1155_count: int = 0
    governance_count: int = 0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _default_repo_root() -> Path:
    """Return the repository root inferred from this module's location."""
    return Path(__file__).resolve().parent.parent


def _is_library_path(path: Path, repo_root: Path) -> bool:
    """Return ``True`` if *path* is inside a vendored library subtree."""
    try:
        relative = path.relative_to(repo_root)
    except ValueError:
        return False
    parts_str = "/".join(relative.parts)
    return any(seg in parts_str for seg in LIBRARY_PATH_SEGMENTS)


def _is_owner_path(path: Path, repo_root: Path) -> bool:
    """Return ``True`` if *path* belongs to a first-party token directory."""
    try:
        relative = path.relative_to(repo_root)
    except ValueError:
        return False
    if not relative.parts:
        return False
    top = relative.parts[0]
    return top in OWNER_TOKEN_DIRECTORIES and not _is_library_path(
        path, repo_root
    )


def _top_directory(path: Path, repo_root: Path) -> str:
    """Return the top-level directory name for *path* relative to *repo_root*."""
    try:
        relative = path.relative_to(repo_root)
    except ValueError:
        return ""
    return relative.parts[0] if relative.parts else ""


def _extract_contract_name(source: str) -> str:
    """Return the first ``contract`` name found in *source*, or empty string."""
    match = _CONTRACT_NAME_RE.search(source)
    return match.group(1) if match else ""


def _detect_token_standards(source: str) -> List[str]:
    """Return the list of token standards detected in *source*.

    Standards are tested in priority order so that more specific ones
    (ERC-1155, ERC-721) are listed before the more general ERC-20.
    Only a contract that *inherits* a standard is classified; a file that
    merely defines or imports an interface is skipped unless its own
    ``contract`` line matches.
    """
    # Gather only the "contract Name is ..." inheritance lines so we don't
    # falsely match import paths or comments.
    inheritance_text = "\n".join(
        line
        for line in source.splitlines()
        if re.search(r"\bcontract\b.*\bis\b", line)
    )
    if not inheritance_text:
        return []

    standards: List[str] = []
    for label, pattern in _STANDARD_PATTERNS.items():
        if pattern.search(inheritance_text):
            standards.append(label)
    return standards


def _classify_file(path: Path, repo_root: Path) -> Optional[TokenAsset]:
    """Read *path* and return a ``TokenAsset`` if it contains a token contract.

    Returns ``None`` if the file cannot be read or contains no token contract.
    """
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    standards = _detect_token_standards(source)
    if not standards:
        return None

    contract_name = _extract_contract_name(source)
    if not contract_name:
        return None

    relative = str(path.relative_to(repo_root))
    owner = _is_owner_path(path, repo_root)
    top_dir = _top_directory(path, repo_root)

    return TokenAsset(
        relative_path=relative,
        contract_name=contract_name,
        token_standards=standards,
        is_owner_contract=owner,
        top_directory=top_dir,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def find_token_assets(
    repo_root: Optional[Path] = None,
) -> TokenAssetInventory:
    """Scan *repo_root* for Solidity token contracts and return an inventory.

    Parameters
    ----------
    repo_root:
        Repository root to scan.  Defaults to the directory that contains
        this module's parent package.

    Returns
    -------
    :class:`TokenAssetInventory`
        Read-only inventory of all discovered token/NFT contracts.
    """
    resolved_root = (repo_root or _default_repo_root()).resolve()

    all_sol_files = list(resolved_root.rglob("*.sol"))
    total_scanned = len(all_sol_files)

    owner_contracts: List[TokenAsset] = []
    protocol_contracts: List[TokenAsset] = []

    for sol_file in sorted(all_sol_files):
        asset = _classify_file(sol_file, resolved_root)
        if asset is None:
            continue
        if asset.is_owner_contract:
            owner_contracts.append(asset)
        else:
            protocol_contracts.append(asset)

    all_assets = owner_contracts + protocol_contracts
    erc20_count = sum(1 for a in all_assets if "ERC-20" in a.token_standards)
    erc721_count = sum(1 for a in all_assets if "ERC-721" in a.token_standards)
    erc1155_count = sum(
        1 for a in all_assets if "ERC-1155" in a.token_standards
    )
    governance_count = sum(
        1 for a in all_assets if "Governance" in a.token_standards
    )

    return TokenAssetInventory(
        repo_root=str(resolved_root),
        owner_contracts=owner_contracts,
        protocol_contracts=protocol_contracts,
        total_solidity_files_scanned=total_scanned,
        erc20_count=erc20_count,
        erc721_count=erc721_count,
        erc1155_count=erc1155_count,
        governance_count=governance_count,
    )


# ---------------------------------------------------------------------------
# Report renderer
# ---------------------------------------------------------------------------


def _render_asset_row(asset: TokenAsset) -> str:
    standards = ", ".join(asset.token_standards) or "other"
    return f"  [{standards}]  {asset.contract_name}  →  {asset.relative_path}"


def render_asset_report(inventory: TokenAssetInventory) -> str:
    """Render a human-readable asset report from *inventory*.

    Parameters
    ----------
    inventory:
        The :class:`TokenAssetInventory` returned by :func:`find_token_assets`.

    Returns
    -------
    str
        A formatted multi-line report suitable for CLI or log output.
    """
    lines = [
        "╔══════════════════════════════════════════════════════════╗",
        "║  NEXUS PROTOCOL — TOKEN & CONTRACT ASSET FINDER          ║",
        "║  @FuzzysTodd  |  All token contracts located             ║",
        "╚══════════════════════════════════════════════════════════╝",
        "",
        f"  Repo root              : {inventory.repo_root}",
        f"  Solidity files scanned : {inventory.total_solidity_files_scanned}",
        "",
        "  ── Token Standard Breakdown ──",
        f"  ERC-20     : {inventory.erc20_count}",
        f"  ERC-721    : {inventory.erc721_count}",
        f"  ERC-1155   : {inventory.erc1155_count}",
        f"  Governance : {inventory.governance_count}",
        "",
        f"  ── Owner / First-Party Token Contracts"
        f" ({len(inventory.owner_contracts)}) ──",
    ]

    if inventory.owner_contracts:
        for asset in inventory.owner_contracts:
            lines.append(_render_asset_row(asset))
    else:
        lines.append("  (none found)")

    lines += [
        "",
        f"  ── Protocol / Third-Party Token Contracts"
        f" ({len(inventory.protocol_contracts)}) ──",
    ]

    # Group protocol contracts by top-level directory for readability.
    grouped: dict[str, List[TokenAsset]] = {}
    for asset in inventory.protocol_contracts:
        grouped.setdefault(asset.top_directory, []).append(asset)

    if grouped:
        for top_dir in sorted(grouped):
            lines.append(f"  [{top_dir}]")
            for asset in grouped[top_dir]:
                lines.append("  " + _render_asset_row(asset))
    else:
        lines.append("  (none found)")

    lines += [
        "",
        "═══════════════════════════════════════════════════════════",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _main() -> None:  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(
        description="Locate all token contracts in the Nexus Protocol repository."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repository root to scan (default: auto-detected).",
    )
    args = parser.parse_args()

    inventory = find_token_assets(repo_root=args.root)
    print(render_asset_report(inventory))


if __name__ == "__main__":  # pragma: no cover
    _main()
