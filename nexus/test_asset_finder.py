"""Tests for the token and contract asset finder."""

from __future__ import annotations

from nexus.asset_finder import (
    _detect_token_standards,
    _extract_contract_name,
    _is_library_path,
    _is_owner_path,
    find_token_assets,
    render_asset_report,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ERC20_SOL = """\
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
contract MyToken is ERC20 {
    constructor() ERC20("My Token", "MTK") {}
}
"""

_ERC721_SOL = """\
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
contract MyNFT is ERC721 {
    constructor() ERC721("My NFT", "MNFT") {}
}
"""

_ERC1155_SOL = """\
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
contract MyMultiToken is ERC1155 {
    constructor() ERC1155("uri") {}
}
"""

_GOVERNANCE_SOL = """\
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol";
contract VoteToken is ERC20Votes {
    constructor() ERC20("Vote", "VOTE") {}
}
"""

_NO_TOKEN_SOL = """\
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
contract SimpleStorage {
    uint256 public value;
}
"""

_COMBO_SOL = """\
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
contract HybridToken is ERC20, ERC721 {
    constructor() {}
}
"""


# ---------------------------------------------------------------------------
# Tests: _detect_token_standards
# ---------------------------------------------------------------------------


def test_erc20_standard_detected(tmp_path):
    (tmp_path / "contracts").mkdir()
    (tmp_path / "contracts" / "Token.sol").write_text(_ERC20_SOL)
    inventory = find_token_assets(repo_root=tmp_path)
    assert inventory.erc20_count == 1
    assert inventory.erc721_count == 0


def test_erc721_standard_detected(tmp_path):
    (tmp_path / "contracts").mkdir()
    (tmp_path / "contracts" / "NFT.sol").write_text(_ERC721_SOL)
    inventory = find_token_assets(repo_root=tmp_path)
    assert inventory.erc721_count == 1
    assert inventory.erc20_count == 0


def test_erc1155_standard_detected(tmp_path):
    (tmp_path / "contracts").mkdir()
    (tmp_path / "contracts" / "Multi.sol").write_text(_ERC1155_SOL)
    inventory = find_token_assets(repo_root=tmp_path)
    assert inventory.erc1155_count == 1


def test_governance_standard_detected(tmp_path):
    (tmp_path / "voting-token").mkdir()
    (tmp_path / "voting-token" / "vote.sol").write_text(_GOVERNANCE_SOL)
    inventory = find_token_assets(repo_root=tmp_path)
    assert inventory.governance_count == 1


def test_non_token_contract_not_counted(tmp_path):
    (tmp_path / "contracts").mkdir()
    (tmp_path / "contracts" / "Storage.sol").write_text(_NO_TOKEN_SOL)
    inventory = find_token_assets(repo_root=tmp_path)
    assert inventory.erc20_count == 0
    assert inventory.erc721_count == 0
    assert inventory.owner_contracts == []
    assert inventory.protocol_contracts == []


def test_combined_standards_in_one_contract(tmp_path):
    (tmp_path / "contracts").mkdir()
    (tmp_path / "contracts" / "Combo.sol").write_text(_COMBO_SOL)
    inventory = find_token_assets(repo_root=tmp_path)
    assert inventory.erc20_count == 1
    assert inventory.erc721_count == 1


# ---------------------------------------------------------------------------
# Tests: owner vs. protocol classification
# ---------------------------------------------------------------------------


def test_owner_contract_classified_correctly(tmp_path):
    (tmp_path / "mintable-token").mkdir()
    (tmp_path / "mintable-token" / "mintable-token.sol").write_text(_ERC20_SOL)
    inventory = find_token_assets(repo_root=tmp_path)
    assert len(inventory.owner_contracts) == 1
    assert inventory.owner_contracts[0].is_owner_contract is True
    assert inventory.protocol_contracts == []


def test_protocol_contract_classified_correctly(tmp_path):
    (tmp_path / "Uniswap-V2").mkdir()
    (tmp_path / "Uniswap-V2" / "UniswapERC20.sol").write_text(_ERC20_SOL)
    inventory = find_token_assets(repo_root=tmp_path)
    assert len(inventory.protocol_contracts) == 1
    assert inventory.protocol_contracts[0].is_owner_contract is False
    assert inventory.owner_contracts == []


def test_openzeppelin_library_excluded_from_owner(tmp_path):
    oz_dir = tmp_path / "mintable-token" / "@openzeppelin" / "contracts" / "token" / "ERC20"
    oz_dir.mkdir(parents=True)
    (oz_dir / "ERC20.sol").write_text(_ERC20_SOL)
    # The bundled library copy must not appear as an owner contract.
    inventory = find_token_assets(repo_root=tmp_path)
    for asset in inventory.owner_contracts:
        assert "@openzeppelin" not in asset.relative_path


def test_contracts_directory_is_owner(tmp_path):
    (tmp_path / "contracts").mkdir()
    (tmp_path / "contracts" / "NexusToken.sol").write_text(_ERC20_SOL)
    inventory = find_token_assets(repo_root=tmp_path)
    assert len(inventory.owner_contracts) == 1
    assert inventory.owner_contracts[0].top_directory == "contracts"


# ---------------------------------------------------------------------------
# Tests: inventory totals
# ---------------------------------------------------------------------------


def test_total_solidity_files_scanned_includes_non_token(tmp_path):
    (tmp_path / "contracts").mkdir()
    (tmp_path / "contracts" / "Token.sol").write_text(_ERC20_SOL)
    (tmp_path / "contracts" / "Storage.sol").write_text(_NO_TOKEN_SOL)
    inventory = find_token_assets(repo_root=tmp_path)
    assert inventory.total_solidity_files_scanned == 2


def test_empty_repo_returns_empty_inventory(tmp_path):
    inventory = find_token_assets(repo_root=tmp_path)
    assert inventory.owner_contracts == []
    assert inventory.protocol_contracts == []
    assert inventory.total_solidity_files_scanned == 0
    assert inventory.erc20_count == 0


# ---------------------------------------------------------------------------
# Tests: render_asset_report
# ---------------------------------------------------------------------------


def test_render_report_contains_header_and_owner_section(tmp_path):
    (tmp_path / "contracts").mkdir()
    (tmp_path / "contracts" / "MyToken.sol").write_text(_ERC20_SOL)
    inventory = find_token_assets(repo_root=tmp_path)
    report = render_asset_report(inventory)
    assert "NEXUS PROTOCOL" in report
    assert "TOKEN & CONTRACT ASSET FINDER" in report
    assert "Owner / First-Party" in report
    assert "MyToken" in report


def test_render_report_groups_protocol_by_directory(tmp_path):
    (tmp_path / "Uniswap-V3").mkdir()
    (tmp_path / "Uniswap-V3" / "Token.sol").write_text(_ERC20_SOL)
    inventory = find_token_assets(repo_root=tmp_path)
    report = render_asset_report(inventory)
    assert "Uniswap-V3" in report


def test_render_report_shows_standard_breakdown(tmp_path):
    (tmp_path / "contracts").mkdir()
    (tmp_path / "contracts" / "T.sol").write_text(_ERC20_SOL)
    inventory = find_token_assets(repo_root=tmp_path)
    report = render_asset_report(inventory)
    assert "ERC-20" in report
    assert "ERC-721" in report


def test_render_report_shows_none_found_when_empty(tmp_path):
    inventory = find_token_assets(repo_root=tmp_path)
    report = render_asset_report(inventory)
    assert "(none found)" in report


# ---------------------------------------------------------------------------
# Tests: TokenAsset contract name extraction
# ---------------------------------------------------------------------------


def test_contract_name_extracted_correctly(tmp_path):
    (tmp_path / "contracts").mkdir()
    (tmp_path / "contracts" / "SpecialToken.sol").write_text(_ERC20_SOL)
    inventory = find_token_assets(repo_root=tmp_path)
    names = [a.contract_name for a in inventory.owner_contracts]
    assert "MyToken" in names


def test_relative_path_recorded(tmp_path):
    (tmp_path / "contracts").mkdir()
    (tmp_path / "contracts" / "SpecialToken.sol").write_text(_ERC20_SOL)
    inventory = find_token_assets(repo_root=tmp_path)
    paths = [a.relative_path for a in inventory.owner_contracts]
    assert any("SpecialToken.sol" in p for p in paths)


# ---------------------------------------------------------------------------
# Tests: internal helper functions
# ---------------------------------------------------------------------------

_ABSTRACT_ERC20_SOL = """\
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
abstract contract AbstractToken is ERC20 {
    function doSomething() external virtual;
}
"""

_NO_INHERITANCE_SOL = """\
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
contract JustStorage {
    uint256 public val;
}
"""


def test_extract_contract_name_from_abstract_contract():
    name = _extract_contract_name(_ABSTRACT_ERC20_SOL)
    assert name == "AbstractToken"


def test_extract_contract_name_from_regular_contract():
    name = _extract_contract_name(_ERC20_SOL)
    assert name == "MyToken"


def test_extract_contract_name_empty_source():
    assert _extract_contract_name("pragma solidity ^0.8.0;") == ""


def test_detect_token_standards_no_inheritance_returns_empty():
    # A contract with no "contract X is Y" line should yield no standards
    standards = _detect_token_standards(_NO_INHERITANCE_SOL)
    assert standards == []


def test_detect_token_standards_erc20_detected_directly():
    standards = _detect_token_standards(_ERC20_SOL)
    assert "ERC-20" in standards


def test_detect_token_standards_erc721_not_in_erc20_source():
    standards = _detect_token_standards(_ERC20_SOL)
    assert "ERC-721" not in standards


def test_is_library_path_true_for_openzeppelin(tmp_path):
    oz = tmp_path / "mintable-token" / "@openzeppelin" / "contracts" / "ERC20.sol"
    oz.parent.mkdir(parents=True)
    oz.touch()
    assert _is_library_path(oz, tmp_path) is True


def test_is_library_path_false_for_first_party(tmp_path):
    first = tmp_path / "contracts" / "MyToken.sol"
    first.parent.mkdir()
    first.touch()
    assert _is_library_path(first, tmp_path) is False


def test_is_owner_path_true_for_contracts_dir(tmp_path):
    sol = tmp_path / "contracts" / "Token.sol"
    sol.parent.mkdir()
    sol.touch()
    assert _is_owner_path(sol, tmp_path) is True


def test_is_owner_path_false_for_protocol_dir(tmp_path):
    sol = tmp_path / "Uniswap-V3" / "UniswapV3Pool.sol"
    sol.parent.mkdir()
    sol.touch()
    assert _is_owner_path(sol, tmp_path) is False


def test_is_owner_path_false_for_library_inside_owner_dir(tmp_path):
    oz = tmp_path / "mintable-token" / "@openzeppelin" / "ERC20.sol"
    oz.parent.mkdir(parents=True)
    oz.touch()
    assert _is_owner_path(oz, tmp_path) is False
