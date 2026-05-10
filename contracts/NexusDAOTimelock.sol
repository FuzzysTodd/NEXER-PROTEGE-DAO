// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/governance/TimelockController.sol";

/// @title NexusDAOTimelock
/// @notice Timelock controller for the Nexus Protocol DAO governance stack.
/// @dev Wraps OpenZeppelin TimelockController with Nexus-specific documentation and
///      enforces the minimum 2-day delay mandated by the Nexus Governance charter.
///      NES: this contract is a Nexus-authored surface governed by the
///      Nexus Encryption Standard as documented in docs/NEXUS_ENCRYPTION_STANDARD.md.
///
/// Deployment recipe:
///   1. Deploy NexusDAOTimelock with minDelay = 172800 (2 days), proposers = [governor],
///      executors = [address(0)] (anyone may execute after delay), admin = owner wallet.
///   2. After the Governor is deployed and the Timelock's PROPOSER_ROLE is granted to
///      the Governor, revoke TIMELOCK_ADMIN_ROLE from the deployer to make the
///      Timelock fully self-administered.
///
/// Access roles (inherited from OpenZeppelin TimelockController):
///   - TIMELOCK_ADMIN_ROLE  : can manage roles; should be renounced post-setup.
///   - PROPOSER_ROLE        : granted to the NexusDAOGovernor.
///   - EXECUTOR_ROLE        : granted to address(0) for permissionless execution.
///   - CANCELLER_ROLE       : granted to Owner and/or Super Delegates for emergency use.
contract NexusDAOTimelock is TimelockController {
    /// @notice Minimum enforced delay in seconds (2 days).
    uint256 public constant MIN_ENFORCED_DELAY = 2 days;

    /// @notice Emitted once during construction to record the deployment parameters.
    event TimelockDeployed(uint256 minDelay, uint256 proposerCount, uint256 executorCount);

    /// @notice Deploys the timelock.
    /// @param minDelay Minimum seconds between queuing and execution.
    ///        Must be at least MIN_ENFORCED_DELAY (172 800 seconds).
    /// @param proposers Addresses granted PROPOSER_ROLE (typically [governor]).
    /// @param executors Addresses granted EXECUTOR_ROLE.
    ///        Pass [address(0)] to allow any address to execute ready operations.
    /// @param admin Address granted TIMELOCK_ADMIN_ROLE for initial role setup.
    ///        Should call renounceRole(TIMELOCK_ADMIN_ROLE, admin) after setup.
    constructor(
        uint256 minDelay,
        address[] memory proposers,
        address[] memory executors,
        address admin
    ) TimelockController(minDelay, proposers, executors, admin) {
        require(minDelay >= MIN_ENFORCED_DELAY, "NexusDAOTimelock: delay below minimum");
        emit TimelockDeployed(minDelay, proposers.length, executors.length);
    }
}
