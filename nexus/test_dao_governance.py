"""
Structural and security tests for the Nexus Protocol DAO governance contracts.

These tests validate:
  - All four governance contract files are present.
  - Correct Solidity pragma (^0.8.20) and SPDX identifier.
  - Required OpenZeppelin imports are declared.
  - Key functions, events, modifiers, and constants are present.
  - NatSpec documentation exists on public/external functions.
  - No hard-coded secrets or private key placeholders.
  - Security invariants: reentrancy guards, access-control modifiers, SafeERC20.
  - Governance architecture consistency (governor references timelock and token).
  - Deploy script and documentation are present and well-formed.

These tests do NOT compile or execute Solidity on-chain; they analyse the
source text to catch structural regressions, missing security primitives, and
documentation gaps early in the development cycle.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = REPO_ROOT / "contracts"
SCRIPTS = REPO_ROOT / "scripts"
DOCS = REPO_ROOT / "docs"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_sol(name: str) -> str:
    return (CONTRACTS / name).read_text()


def has_function(source: str, func_name: str) -> bool:
    """Return True if `source` contains a Solidity function with the given name."""
    return bool(re.search(rf"\bfunction\s+{re.escape(func_name)}\b", source))


def has_event(source: str, event_name: str) -> bool:
    return bool(re.search(rf"\bevent\s+{re.escape(event_name)}\b", source))


def has_modifier(source: str, modifier_name: str) -> bool:
    return bool(re.search(rf"\b{re.escape(modifier_name)}\b", source))


def has_natspec(source: str, func_name: str) -> bool:
    """Return True if a @notice or @dev comment appears near the function."""
    idx = source.find(f"function {func_name}")
    if idx == -1:
        return False
    snippet = source[max(0, idx - 500):idx]
    return "/// @notice" in snippet or "/// @dev" in snippet or "* @notice" in snippet


# ---------------------------------------------------------------------------
# NGTTGovernanceToken.sol — existence and pragma
# ---------------------------------------------------------------------------

def test_ngtt_governance_token_file_exists():
    assert (CONTRACTS / "NGTTGovernanceToken.sol").is_file()


def test_ngtt_governance_token_pragma():
    src = read_sol("NGTTGovernanceToken.sol")
    assert "pragma solidity ^0.8.20;" in src


def test_ngtt_governance_token_spdx():
    src = read_sol("NGTTGovernanceToken.sol")
    assert "SPDX-License-Identifier: MIT" in src


# ---------------------------------------------------------------------------
# NGTTGovernanceToken.sol — OZ imports
# ---------------------------------------------------------------------------

def test_ngtt_imports_erc20votes():
    src = read_sol("NGTTGovernanceToken.sol")
    assert "ERC20Votes" in src


def test_ngtt_imports_erc20permit():
    src = read_sol("NGTTGovernanceToken.sol")
    # draft-ERC20Permit is part of ERC20Votes inheritance chain; name appears in import
    assert "ERC20Permit" in src


def test_ngtt_imports_ownable():
    src = read_sol("NGTTGovernanceToken.sol")
    assert "Ownable" in src


def test_ngtt_imports_reentrancy_guard():
    src = read_sol("NGTTGovernanceToken.sol")
    assert "ReentrancyGuard" in src


# ---------------------------------------------------------------------------
# NGTTGovernanceToken.sol — constants
# ---------------------------------------------------------------------------

def test_ngtt_initial_supply_constant():
    src = read_sol("NGTTGovernanceToken.sol")
    assert "INITIAL_SUPPLY" in src
    assert "1_000_000_000" in src


def test_ngtt_btc_backing_ratio_constant():
    src = read_sol("NGTTGovernanceToken.sol")
    assert "BTC_BACKING_RATIO" in src


# ---------------------------------------------------------------------------
# NGTTGovernanceToken.sol — core functions
# ---------------------------------------------------------------------------

def test_ngtt_has_constructor():
    src = read_sol("NGTTGovernanceToken.sol")
    assert "constructor()" in src


def test_ngtt_has_create_mcp_group():
    assert has_function(read_sol("NGTTGovernanceToken.sol"), "createMCPGroup")


def test_ngtt_has_complete_game():
    assert has_function(read_sol("NGTTGovernanceToken.sol"), "completeGame")


def test_ngtt_has_distribute_profits():
    assert has_function(read_sol("NGTTGovernanceToken.sol"), "distributeProfits")


def test_ngtt_has_claim_profits():
    assert has_function(read_sol("NGTTGovernanceToken.sol"), "claimProfits")


def test_ngtt_has_add_profit_pool():
    assert has_function(read_sol("NGTTGovernanceToken.sol"), "addProfitPool")


def test_ngtt_has_activate_boost():
    assert has_function(read_sol("NGTTGovernanceToken.sol"), "activateBoost")


def test_ngtt_has_get_user_stats():
    assert has_function(read_sol("NGTTGovernanceToken.sol"), "getUserStats")


def test_ngtt_has_get_group_stats():
    assert has_function(read_sol("NGTTGovernanceToken.sol"), "getGroupStats")


# ---------------------------------------------------------------------------
# NGTTGovernanceToken.sol — ERC20Votes override functions
# ---------------------------------------------------------------------------

def test_ngtt_overrides_after_token_transfer():
    assert has_function(read_sol("NGTTGovernanceToken.sol"), "_afterTokenTransfer")


def test_ngtt_overrides_mint():
    assert has_function(read_sol("NGTTGovernanceToken.sol"), "_mint")


def test_ngtt_overrides_burn():
    assert has_function(read_sol("NGTTGovernanceToken.sol"), "_burn")


# ---------------------------------------------------------------------------
# NGTTGovernanceToken.sol — events
# ---------------------------------------------------------------------------

def test_ngtt_event_mcp_group_created():
    assert has_event(read_sol("NGTTGovernanceToken.sol"), "MCPGroupCreated")


def test_ngtt_event_game_completed():
    assert has_event(read_sol("NGTTGovernanceToken.sol"), "GameCompleted")


def test_ngtt_event_profit_distributed():
    assert has_event(read_sol("NGTTGovernanceToken.sol"), "ProfitDistributed")


def test_ngtt_event_boost_activated():
    assert has_event(read_sol("NGTTGovernanceToken.sol"), "BoostActivated")


def test_ngtt_event_profit_pool_increased():
    assert has_event(read_sol("NGTTGovernanceToken.sol"), "ProfitPoolIncreased")


# ---------------------------------------------------------------------------
# NGTTGovernanceToken.sol — security
# ---------------------------------------------------------------------------

def test_ngtt_uses_nonreentrant_on_complete_game():
    src = read_sol("NGTTGovernanceToken.sol")
    # nonReentrant must appear near the completeGame function signature
    idx = src.find("function completeGame")
    assert idx != -1
    snippet = src[idx: idx + 200]
    assert "nonReentrant" in snippet


def test_ngtt_uses_nonreentrant_on_claim_profits():
    src = read_sol("NGTTGovernanceToken.sol")
    idx = src.find("function claimProfits")
    assert idx != -1
    snippet = src[idx: idx + 200]
    assert "nonReentrant" in snippet


def test_ngtt_uses_nonreentrant_on_distribute_profits():
    src = read_sol("NGTTGovernanceToken.sol")
    idx = src.find("function distributeProfits")
    assert idx != -1
    snippet = src[idx: idx + 200]
    assert "nonReentrant" in snippet


def test_ngtt_no_private_key_literals():
    src = read_sol("NGTTGovernanceToken.sol")
    assert "PRIVATE_KEY" not in src
    assert "mnemonic" not in src.lower()


def test_ngtt_no_tx_origin_auth():
    src = read_sol("NGTTGovernanceToken.sol")
    # tx.origin must not be used for authentication
    assert "tx.origin" not in src


# ---------------------------------------------------------------------------
# NGTTGovernanceToken.sol — NatSpec
# ---------------------------------------------------------------------------

def test_ngtt_natspec_on_constructor():
    src = read_sol("NGTTGovernanceToken.sol")
    assert "/// @notice" in src


def test_ngtt_natspec_on_create_mcp_group():
    assert has_natspec(read_sol("NGTTGovernanceToken.sol"), "createMCPGroup")


def test_ngtt_natspec_on_complete_game():
    assert has_natspec(read_sol("NGTTGovernanceToken.sol"), "completeGame")


def test_ngtt_natspec_on_claim_profits():
    assert has_natspec(read_sol("NGTTGovernanceToken.sol"), "claimProfits")


def test_ngtt_natspec_on_get_user_stats():
    assert has_natspec(read_sol("NGTTGovernanceToken.sol"), "getUserStats")


# ---------------------------------------------------------------------------
# NGTTGovernanceToken.sol — governance architecture
# ---------------------------------------------------------------------------

def test_ngtt_inherits_erc20votes():
    src = read_sol("NGTTGovernanceToken.sol")
    assert "ERC20Votes" in src
    # Contract declaration must include ERC20Votes in the inheritance list
    contract_line = next(
        (line for line in src.splitlines() if line.strip().startswith("contract NGTTGovernanceToken")), ""
    )
    assert "ERC20Votes" in contract_line


def test_ngtt_self_delegates_in_constructor():
    src = read_sol("NGTTGovernanceToken.sol")
    # Constructor must set up initial delegation
    ctor_idx = src.find("constructor()")
    assert ctor_idx != -1
    ctor_body = src[ctor_idx: ctor_idx + 400]
    assert "_delegate" in ctor_body or "delegate" in ctor_body


# ---------------------------------------------------------------------------
# NexusDAOTimelock.sol — existence and pragma
# ---------------------------------------------------------------------------

def test_nexus_dao_timelock_file_exists():
    assert (CONTRACTS / "NexusDAOTimelock.sol").is_file()


def test_nexus_dao_timelock_pragma():
    src = read_sol("NexusDAOTimelock.sol")
    assert "pragma solidity ^0.8.20;" in src


def test_nexus_dao_timelock_spdx():
    src = read_sol("NexusDAOTimelock.sol")
    assert "SPDX-License-Identifier: MIT" in src


# ---------------------------------------------------------------------------
# NexusDAOTimelock.sol — imports and inheritance
# ---------------------------------------------------------------------------

def test_nexus_dao_timelock_imports_oz():
    src = read_sol("NexusDAOTimelock.sol")
    assert "TimelockController" in src


def test_nexus_dao_timelock_inherits_timelock_controller():
    src = read_sol("NexusDAOTimelock.sol")
    contract_line = next(
        (line for line in src.splitlines() if line.strip().startswith("contract NexusDAOTimelock")), ""
    )
    assert "TimelockController" in contract_line


# ---------------------------------------------------------------------------
# NexusDAOTimelock.sol — enforced minimum delay
# ---------------------------------------------------------------------------

def test_nexus_dao_timelock_has_min_enforced_delay_constant():
    src = read_sol("NexusDAOTimelock.sol")
    assert "MIN_ENFORCED_DELAY" in src


def test_nexus_dao_timelock_enforces_min_delay_in_constructor():
    src = read_sol("NexusDAOTimelock.sol")
    assert "MIN_ENFORCED_DELAY" in src
    assert "require" in src


def test_nexus_dao_timelock_delay_is_two_days():
    src = read_sol("NexusDAOTimelock.sol")
    assert "2 days" in src


# ---------------------------------------------------------------------------
# NexusDAOTimelock.sol — events and NatSpec
# ---------------------------------------------------------------------------

def test_nexus_dao_timelock_has_deployed_event():
    assert has_event(read_sol("NexusDAOTimelock.sol"), "TimelockDeployed")


def test_nexus_dao_timelock_natspec_constructor():
    src = read_sol("NexusDAOTimelock.sol")
    assert "@param minDelay" in src
    assert "@param proposers" in src
    assert "@param executors" in src
    assert "@param admin" in src


# ---------------------------------------------------------------------------
# NexusDAOGovernor.sol — existence and pragma
# ---------------------------------------------------------------------------

def test_nexus_dao_governor_file_exists():
    assert (CONTRACTS / "NexusDAOGovernor.sol").is_file()


def test_nexus_dao_governor_pragma():
    src = read_sol("NexusDAOGovernor.sol")
    assert "pragma solidity ^0.8.20;" in src


def test_nexus_dao_governor_spdx():
    src = read_sol("NexusDAOGovernor.sol")
    assert "SPDX-License-Identifier: MIT" in src


# ---------------------------------------------------------------------------
# NexusDAOGovernor.sol — OZ extensions
# ---------------------------------------------------------------------------

def test_nexus_dao_governor_imports_governor():
    src = read_sol("NexusDAOGovernor.sol")
    assert "Governor" in src


def test_nexus_dao_governor_imports_governor_settings():
    src = read_sol("NexusDAOGovernor.sol")
    assert "GovernorSettings" in src


def test_nexus_dao_governor_imports_governor_votes():
    src = read_sol("NexusDAOGovernor.sol")
    assert "GovernorVotes" in src


def test_nexus_dao_governor_imports_governor_quorum():
    src = read_sol("NexusDAOGovernor.sol")
    assert "GovernorVotesQuorumFraction" in src


def test_nexus_dao_governor_imports_governor_timelock():
    src = read_sol("NexusDAOGovernor.sol")
    assert "GovernorTimelockControl" in src


# ---------------------------------------------------------------------------
# NexusDAOGovernor.sol — inheritance
# ---------------------------------------------------------------------------

def test_nexus_dao_governor_inherits_all_extensions():
    src = read_sol("NexusDAOGovernor.sol")
    contract_decl = ""
    for line in src.splitlines():
        contract_decl += line
        if "{" in line:
            break
    assert "GovernorSettings" in contract_decl
    assert "GovernorVotes" in contract_decl
    assert "GovernorVotesQuorumFraction" in contract_decl
    assert "GovernorTimelockControl" in contract_decl


# ---------------------------------------------------------------------------
# NexusDAOGovernor.sol — governance constants
# ---------------------------------------------------------------------------

def test_nexus_dao_governor_default_voting_delay():
    src = read_sol("NexusDAOGovernor.sol")
    assert "DEFAULT_VOTING_DELAY" in src


def test_nexus_dao_governor_default_voting_period():
    src = read_sol("NexusDAOGovernor.sol")
    assert "DEFAULT_VOTING_PERIOD" in src


def test_nexus_dao_governor_default_proposal_threshold():
    src = read_sol("NexusDAOGovernor.sol")
    assert "DEFAULT_PROPOSAL_THRESHOLD" in src
    # Threshold must include 10_000 NGTT expressed with 10 ** 18 precision
    assert "10_000" in src or "10000" in src


def test_nexus_dao_governor_default_quorum_numerator():
    src = read_sol("NexusDAOGovernor.sol")
    assert "DEFAULT_QUORUM_NUMERATOR" in src


# ---------------------------------------------------------------------------
# NexusDAOGovernor.sol — required override functions
# ---------------------------------------------------------------------------

def test_nexus_dao_governor_overrides_proposal_threshold():
    assert has_function(read_sol("NexusDAOGovernor.sol"), "proposalThreshold")


def test_nexus_dao_governor_overrides_quorum():
    assert has_function(read_sol("NexusDAOGovernor.sol"), "quorum")


def test_nexus_dao_governor_overrides_state():
    assert has_function(read_sol("NexusDAOGovernor.sol"), "state")


def test_nexus_dao_governor_overrides_propose():
    assert has_function(read_sol("NexusDAOGovernor.sol"), "propose")


def test_nexus_dao_governor_overrides_execute():
    assert has_function(read_sol("NexusDAOGovernor.sol"), "_execute")


def test_nexus_dao_governor_overrides_cancel():
    assert has_function(read_sol("NexusDAOGovernor.sol"), "_cancel")


def test_nexus_dao_governor_overrides_executor():
    assert has_function(read_sol("NexusDAOGovernor.sol"), "_executor")


def test_nexus_dao_governor_overrides_supports_interface():
    assert has_function(read_sol("NexusDAOGovernor.sol"), "supportsInterface")


# ---------------------------------------------------------------------------
# NexusDAOGovernor.sol — constructor binds token and timelock
# ---------------------------------------------------------------------------

def test_nexus_dao_governor_constructor_accepts_token_and_timelock():
    src = read_sol("NexusDAOGovernor.sol")
    ctor_idx = src.find("constructor(")
    assert ctor_idx != -1
    ctor_sig = src[ctor_idx: ctor_idx + 200]
    assert "IVotes" in ctor_sig or "token" in ctor_sig.lower()
    assert "TimelockController" in ctor_sig or "timelock" in ctor_sig.lower()


def test_nexus_dao_governor_emits_deployed_event():
    assert has_event(read_sol("NexusDAOGovernor.sol"), "GovernorDeployed")


# ---------------------------------------------------------------------------
# NexusDAOTreasury.sol — existence and pragma
# ---------------------------------------------------------------------------

def test_nexus_dao_treasury_file_exists():
    assert (CONTRACTS / "NexusDAOTreasury.sol").is_file()


def test_nexus_dao_treasury_pragma():
    src = read_sol("NexusDAOTreasury.sol")
    assert "pragma solidity ^0.8.20;" in src


def test_nexus_dao_treasury_spdx():
    src = read_sol("NexusDAOTreasury.sol")
    assert "SPDX-License-Identifier: MIT" in src


# ---------------------------------------------------------------------------
# NexusDAOTreasury.sol — OZ imports
# ---------------------------------------------------------------------------

def test_nexus_dao_treasury_imports_access_control():
    src = read_sol("NexusDAOTreasury.sol")
    assert "AccessControl" in src


def test_nexus_dao_treasury_imports_reentrancy_guard():
    src = read_sol("NexusDAOTreasury.sol")
    assert "ReentrancyGuard" in src


def test_nexus_dao_treasury_uses_safe_erc20():
    src = read_sol("NexusDAOTreasury.sol")
    assert "SafeERC20" in src


# ---------------------------------------------------------------------------
# NexusDAOTreasury.sol — roles
# ---------------------------------------------------------------------------

def test_nexus_dao_treasury_has_executor_role():
    src = read_sol("NexusDAOTreasury.sol")
    assert "EXECUTOR_ROLE" in src


def test_nexus_dao_treasury_has_guardian_role():
    src = read_sol("NexusDAOTreasury.sol")
    assert "GUARDIAN_ROLE" in src


# ---------------------------------------------------------------------------
# NexusDAOTreasury.sol — functions
# ---------------------------------------------------------------------------

def test_nexus_dao_treasury_has_transfer_eth():
    assert has_function(read_sol("NexusDAOTreasury.sol"), "transferETH")


def test_nexus_dao_treasury_has_transfer_erc20():
    assert has_function(read_sol("NexusDAOTreasury.sol"), "transferERC20")


def test_nexus_dao_treasury_has_deposit_erc20():
    assert has_function(read_sol("NexusDAOTreasury.sol"), "depositERC20")


def test_nexus_dao_treasury_has_pause():
    assert has_function(read_sol("NexusDAOTreasury.sol"), "pause")


def test_nexus_dao_treasury_has_unpause():
    assert has_function(read_sol("NexusDAOTreasury.sol"), "unpause")


def test_nexus_dao_treasury_has_eth_balance():
    assert has_function(read_sol("NexusDAOTreasury.sol"), "ethBalance")


def test_nexus_dao_treasury_has_token_balance():
    assert has_function(read_sol("NexusDAOTreasury.sol"), "tokenBalance")


def test_nexus_dao_treasury_has_receive_fallback():
    src = read_sol("NexusDAOTreasury.sol")
    assert "receive()" in src


# ---------------------------------------------------------------------------
# NexusDAOTreasury.sol — events
# ---------------------------------------------------------------------------

def test_nexus_dao_treasury_event_eth_deposited():
    assert has_event(read_sol("NexusDAOTreasury.sol"), "ETHDeposited")


def test_nexus_dao_treasury_event_eth_transferred():
    assert has_event(read_sol("NexusDAOTreasury.sol"), "ETHTransferred")


def test_nexus_dao_treasury_event_erc20_deposited():
    assert has_event(read_sol("NexusDAOTreasury.sol"), "ERC20Deposited")


def test_nexus_dao_treasury_event_erc20_transferred():
    assert has_event(read_sol("NexusDAOTreasury.sol"), "ERC20Transferred")


def test_nexus_dao_treasury_event_paused():
    assert has_event(read_sol("NexusDAOTreasury.sol"), "TreasuryPaused")


def test_nexus_dao_treasury_event_unpaused():
    assert has_event(read_sol("NexusDAOTreasury.sol"), "TreasuryUnpaused")


# ---------------------------------------------------------------------------
# NexusDAOTreasury.sol — security
# ---------------------------------------------------------------------------

def test_nexus_dao_treasury_transfer_eth_uses_call_not_transfer():
    src = read_sol("NexusDAOTreasury.sol")
    # Preferred ETH transfer pattern per Solidity instructions
    assert ".call{value:" in src
    assert ".transfer(" not in src or "safeTransfer" in src


def test_nexus_dao_treasury_transfer_eth_guarded_by_executor_role():
    src = read_sol("NexusDAOTreasury.sol")
    idx = src.find("function transferETH")
    assert idx != -1
    snippet = src[idx: idx + 300]
    assert "EXECUTOR_ROLE" in snippet


def test_nexus_dao_treasury_transfer_erc20_guarded_by_executor_role():
    src = read_sol("NexusDAOTreasury.sol")
    idx = src.find("function transferERC20")
    assert idx != -1
    snippet = src[idx: idx + 300]
    assert "EXECUTOR_ROLE" in snippet


def test_nexus_dao_treasury_transfer_eth_uses_nonreentrant():
    src = read_sol("NexusDAOTreasury.sol")
    idx = src.find("function transferETH")
    assert idx != -1
    snippet = src[idx: idx + 300]
    assert "nonReentrant" in snippet


def test_nexus_dao_treasury_transfer_erc20_uses_nonreentrant():
    src = read_sol("NexusDAOTreasury.sol")
    idx = src.find("function transferERC20")
    assert idx != -1
    snippet = src[idx: idx + 300]
    assert "nonReentrant" in snippet


def test_nexus_dao_treasury_no_private_key_literals():
    src = read_sol("NexusDAOTreasury.sol")
    assert "PRIVATE_KEY" not in src
    assert "mnemonic" not in src.lower()


def test_nexus_dao_treasury_uses_safe_transfer_for_erc20():
    src = read_sol("NexusDAOTreasury.sol")
    assert "safeTransfer" in src


def test_nexus_dao_treasury_no_tx_origin():
    src = read_sol("NexusDAOTreasury.sol")
    assert "tx.origin" not in src


# ---------------------------------------------------------------------------
# NexusDAOTreasury.sol — NatSpec
# ---------------------------------------------------------------------------

def test_nexus_dao_treasury_natspec_transfer_eth():
    assert has_natspec(read_sol("NexusDAOTreasury.sol"), "transferETH")


def test_nexus_dao_treasury_natspec_transfer_erc20():
    assert has_natspec(read_sol("NexusDAOTreasury.sol"), "transferERC20")


def test_nexus_dao_treasury_natspec_pause():
    assert has_natspec(read_sol("NexusDAOTreasury.sol"), "pause")


# ---------------------------------------------------------------------------
# Cross-contract architecture consistency
# ---------------------------------------------------------------------------

def test_all_four_contracts_exist():
    for name in [
        "NGTTGovernanceToken.sol",
        "NexusDAOTimelock.sol",
        "NexusDAOGovernor.sol",
        "NexusDAOTreasury.sol",
    ]:
        assert (CONTRACTS / name).is_file(), f"Missing: {name}"


def test_all_contracts_use_0820_pragma():
    for name in [
        "NGTTGovernanceToken.sol",
        "NexusDAOTimelock.sol",
        "NexusDAOGovernor.sol",
        "NexusDAOTreasury.sol",
    ]:
        src = read_sol(name)
        assert "pragma solidity ^0.8.20;" in src, f"Wrong pragma in {name}"


def test_all_contracts_have_mit_license():
    for name in [
        "NGTTGovernanceToken.sol",
        "NexusDAOTimelock.sol",
        "NexusDAOGovernor.sol",
        "NexusDAOTreasury.sol",
    ]:
        src = read_sol(name)
        assert "SPDX-License-Identifier: MIT" in src, f"Missing SPDX in {name}"


def test_all_contracts_reference_nes():
    """Every Nexus-authored contract must include an NES reference."""
    for name in [
        "NGTTGovernanceToken.sol",
        "NexusDAOTimelock.sol",
        "NexusDAOGovernor.sol",
        "NexusDAOTreasury.sol",
    ]:
        src = read_sol(name)
        assert "NES" in src or "Nexus Encryption Standard" in src, (
            f"Missing NES reference in {name}"
        )


def test_governor_references_timelock():
    src = read_sol("NexusDAOGovernor.sol")
    assert "TimelockController" in src or "NexusDAOTimelock" in src


def test_governor_references_ivotes_token():
    src = read_sol("NexusDAOGovernor.sol")
    assert "IVotes" in src


def test_timelock_deploy_event_records_parameters():
    src = read_sol("NexusDAOTimelock.sol")
    # The TimelockDeployed event should capture minDelay and counts
    idx = src.find("event TimelockDeployed")
    assert idx != -1
    event_decl = src[idx: idx + 120]
    assert "minDelay" in event_decl or "uint256" in event_decl


# ---------------------------------------------------------------------------
# Deploy script
# ---------------------------------------------------------------------------

def test_deploy_script_exists():
    assert (SCRIPTS / "deploy_dao.js").is_file()


def test_deploy_script_deploys_all_four_contracts():
    script = (SCRIPTS / "deploy_dao.js").read_text()
    assert "NGTTGovernanceToken" in script
    assert "NexusDAOTimelock" in script
    assert "NexusDAOGovernor" in script
    assert "NexusDAOTreasury" in script


def test_deploy_script_has_role_ceremony():
    script = (SCRIPTS / "deploy_dao.js").read_text()
    assert "PROPOSER_ROLE" in script
    assert "EXECUTOR_ROLE" in script
    assert "revokeRole" in script


def test_deploy_script_transfers_ngtt_ownership_to_timelock():
    script = (SCRIPTS / "deploy_dao.js").read_text()
    assert "transferOwnership" in script
    assert "timelock.address" in script


def test_deploy_script_no_hardcoded_private_keys():
    script = (SCRIPTS / "deploy_dao.js").read_text()
    assert "PRIVATE_KEY" not in script
    assert "mnemonic" not in script.lower()
    assert "0x" + "a" * 64 not in script  # no 64-hex private key literal


def test_deploy_script_documents_next_steps():
    script = (SCRIPTS / "deploy_dao.js").read_text()
    assert "Next steps" in script or "next steps" in script


# ---------------------------------------------------------------------------
# Documentation
# ---------------------------------------------------------------------------

def test_dao_governance_doc_exists():
    assert (DOCS / "DAO_GOVERNANCE_IMPLEMENTATION.md").is_file()


def test_dao_governance_doc_covers_all_contracts():
    doc = (DOCS / "DAO_GOVERNANCE_IMPLEMENTATION.md").read_text()
    assert "NGTTGovernanceToken" in doc
    assert "NexusDAOTimelock" in doc
    assert "NexusDAOGovernor" in doc
    assert "NexusDAOTreasury" in doc


def test_dao_governance_doc_has_deployment_procedure():
    doc = (DOCS / "DAO_GOVERNANCE_IMPLEMENTATION.md").read_text()
    assert "Deployment" in doc


def test_dao_governance_doc_has_security_model():
    doc = (DOCS / "DAO_GOVERNANCE_IMPLEMENTATION.md").read_text()
    assert "Security" in doc or "security" in doc


def test_dao_governance_doc_has_emergency_runbook():
    doc = (DOCS / "DAO_GOVERNANCE_IMPLEMENTATION.md").read_text()
    assert "Emergency" in doc or "emergency" in doc


def test_dao_governance_doc_has_voter_guide():
    doc = (DOCS / "DAO_GOVERNANCE_IMPLEMENTATION.md").read_text()
    assert "delegate" in doc.lower()
    assert "castVote" in doc or "vote" in doc.lower()


def test_dao_governance_doc_references_governance_md():
    doc = (DOCS / "DAO_GOVERNANCE_IMPLEMENTATION.md").read_text()
    assert "GOVERNANCE.md" in doc


def test_dao_governance_doc_mentions_nes():
    doc = (DOCS / "DAO_GOVERNANCE_IMPLEMENTATION.md").read_text()
    assert "NES" in doc or "Nexus Encryption Standard" in doc
