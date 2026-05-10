// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/governance/Governor.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorSettings.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotesQuorumFraction.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorTimelockControl.sol";

/// @title NexusDAOGovernor
/// @notice On-chain governance contract for the Nexus Protocol DAO.
/// @dev Combines four OpenZeppelin Governor extensions:
///      - GovernorSettings        : configurable voting delay, voting period, proposal threshold.
///      - GovernorVotes            : voting weight derived from NGTTGovernanceToken snapshots.
///      - GovernorVotesQuorumFraction : quorum expressed as a fraction of total supply.
///      - GovernorTimelockControl  : all passed proposals are queued in NexusDAOTimelock.
///
///      NES: this contract is a Nexus-authored surface governed by the
///      Nexus Encryption Standard as documented in docs/NEXUS_ENCRYPTION_STANDARD.md.
///
/// Default governance parameters (may be updated via governance):
///   - Voting delay  : 7 200 blocks  (~1 day  at 12 s/block on Ethereum mainnet)
///   - Voting period : 50 400 blocks (~7 days at 12 s/block)
///   - Proposal threshold : 10 000 NGTT (10_000 * 10**18)
///   - Quorum        : 4 % of total token supply at snapshot block
///   - Timelock delay: 2 days (set in NexusDAOTimelock constructor)
///
/// Proposal lifecycle:
///   propose() → [voting delay] → castVote() → [voting period] →
///   queue() → [timelock delay] → execute()
///
/// Emergency controls:
///   - Super Delegates hold CANCELLER_ROLE on the Timelock and may cancel queued
///     operations before execution.
///   - Owner (FuzzysTodd) is the canonical authority per GOVERNANCE.md.
contract NexusDAOGovernor is
    Governor,
    GovernorSettings,
    GovernorVotes,
    GovernorVotesQuorumFraction,
    GovernorTimelockControl
{
    // -------------------------------------------------------------------------
    // Constants
    // -------------------------------------------------------------------------

    /// @notice Default voting delay in blocks (~1 day at 12 s/block).
    uint256 public constant DEFAULT_VOTING_DELAY = 7_200;

    /// @notice Default voting period in blocks (~7 days at 12 s/block).
    uint256 public constant DEFAULT_VOTING_PERIOD = 50_400;

    /// @notice Default proposal threshold: 10 000 NGTT (18 decimals).
    uint256 public constant DEFAULT_PROPOSAL_THRESHOLD = 10_000 * 10 ** 18;

    /// @notice Default quorum numerator: 4 % of total token supply.
    uint256 public constant DEFAULT_QUORUM_NUMERATOR = 4;

    /// @notice Minimum allowed quorum numerator (1 %).
    ///         Prevents governance from setting an effectively zero quorum.
    uint256 public constant MIN_QUORUM_NUMERATOR = 1;

    /// @notice Maximum allowed quorum numerator (20 %).
    ///         Prevents governance from setting an impossible-to-reach quorum.
    uint256 public constant MAX_QUORUM_NUMERATOR = 20;

    // -------------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------------

    /// @notice Emitted when the governor is first deployed.
    event GovernorDeployed(address token, address timelock);

    // -------------------------------------------------------------------------
    // Constructor
    // -------------------------------------------------------------------------

    /// @notice Deploys the governor bound to a specific votes token and timelock.
    /// @param _token  Address of the NGTTGovernanceToken (must implement IVotes).
    /// @param _timelock Address of the NexusDAOTimelock.
    constructor(IVotes _token, TimelockController _timelock)
        Governor("NexusDAOGovernor")
        GovernorSettings(
            DEFAULT_VOTING_DELAY,
            DEFAULT_VOTING_PERIOD,
            DEFAULT_PROPOSAL_THRESHOLD
        )
        GovernorVotes(_token)
        GovernorVotesQuorumFraction(DEFAULT_QUORUM_NUMERATOR)
        GovernorTimelockControl(_timelock)
    {
        emit GovernorDeployed(address(_token), address(_timelock));
    }

    // -------------------------------------------------------------------------
    // Required overrides — Solidity multi-inheritance resolution
    // -------------------------------------------------------------------------

    /// @notice Returns the number of votes required to submit a proposal.
    /// @return Proposal threshold in NGTT (18 decimals).
    function proposalThreshold()
        public
        view
        override(Governor, GovernorSettings)
        returns (uint256)
    {
        return super.proposalThreshold();
    }

    /// @notice Returns the quorum required for a proposal at a given block.
    /// @param blockNumber The snapshot block.
    /// @return Minimum votes-for required.
    function quorum(uint256 blockNumber)
        public
        view
        override(IGovernor, GovernorVotesQuorumFraction)
        returns (uint256)
    {
        return super.quorum(blockNumber);
    }

    /// @notice Returns the execution state of a proposal.
    /// @param proposalId Unique identifier of the proposal.
    /// @return Current ProposalState enum value.
    function state(uint256 proposalId)
        public
        view
        override(Governor, GovernorTimelockControl)
        returns (ProposalState)
    {
        return super.state(proposalId);
    }

    /// @notice Queues a passed proposal in the timelock for delayed execution.
    /// @param targets  Call targets.
    /// @param values   ETH values.
    /// @param calldatas Encoded call data.
    /// @param descriptionHash keccak256 of the proposal description.
    /// @return proposalId Unique proposal identifier.
    function propose(
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        string memory description
    ) public override(Governor, IGovernor) returns (uint256) {
        return super.propose(targets, values, calldatas, description);
    }

    /// @dev Internal execution hook — forwards to GovernorTimelockControl.
    function _execute(
        uint256 proposalId,
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        bytes32 descriptionHash
    ) internal override(Governor, GovernorTimelockControl) {
        super._execute(proposalId, targets, values, calldatas, descriptionHash);
    }

    /// @dev Internal cancel hook — forwards to GovernorTimelockControl.
    function _cancel(
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        bytes32 descriptionHash
    ) internal override(Governor, GovernorTimelockControl) returns (uint256) {
        return super._cancel(targets, values, calldatas, descriptionHash);
    }

    /// @dev Returns the executor address (the timelock contract).
    function _executor()
        internal
        view
        override(Governor, GovernorTimelockControl)
        returns (address)
    {
        return super._executor();
    }

    /// @notice Checks interface support including the timelock extension.
    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(Governor, GovernorTimelockControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }

    // -------------------------------------------------------------------------
    // Quorum governance (bounded update)
    // -------------------------------------------------------------------------

    /// @notice Updates the quorum numerator via a governance proposal.
    /// @dev Overrides GovernorVotesQuorumFraction to enforce Nexus bounds
    ///      [MIN_QUORUM_NUMERATOR, MAX_QUORUM_NUMERATOR].  Callable only
    ///      through a successful on-chain governance vote (msg.sender must be
    ///      the governor itself, i.e. called via timelock execution).
    /// @param newQuorumNumerator New quorum percentage (1–20 inclusive).
    function updateQuorumNumerator(uint256 newQuorumNumerator)
        public
        override
    {
        require(
            newQuorumNumerator >= MIN_QUORUM_NUMERATOR,
            "NexusDAOGovernor: quorum below minimum"
        );
        require(
            newQuorumNumerator <= MAX_QUORUM_NUMERATOR,
            "NexusDAOGovernor: quorum above maximum"
        );
        super.updateQuorumNumerator(newQuorumNumerator);
    }
}
