// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title NexusToken (NGTT)
 * @notice Nexus Protocol governance + utility token.
 *         - ERC-20Votes: on-chain delegation and vote weight snapshots for Governor
 *         - ERC-20Permit: gas-less approvals (EIP-2612)
 *         - AccessControl: MINTER_ROLE / PAUSER_ROLE segregation
 *         - GameCompleted / ProfitDistributed events consumed by the Signal Bus
 *
 * Agent assignments (MIG network):
 *   mcp-002 Token Economics Manager  — oversees supply caps and distribution
 *   mcp-003 DAO Governance Agent     — uses vote snapshots
 *   mcp-004 AI Data Pipeline Manager — consumes GameCompleted events
 *
 * @author Nexus Protocol DAO  (nexus-crypto-core · nexus-dao-counsel)
 */
contract NexusToken is ERC20Votes, ERC20Permit, AccessControl, Pausable {
    // -----------------------------------------------------------------------
    // Roles
    // -----------------------------------------------------------------------
    bytes32 public constant MINTER_ROLE  = keccak256("MINTER_ROLE");
    bytes32 public constant PAUSER_ROLE  = keccak256("PAUSER_ROLE");
    bytes32 public constant GAME_ROLE    = keccak256("GAME_ROLE");

    // -----------------------------------------------------------------------
    // Supply parameters
    // -----------------------------------------------------------------------
    uint256 public constant MAX_SUPPLY = 1_000_000_000 * 1e18; // 1 billion NGTT

    // -----------------------------------------------------------------------
    // Game / profit events (consumed by nexus-signal-bus.js)
    // -----------------------------------------------------------------------
    event GameCompleted(
        address indexed player,
        uint256 reward,
        uint256 skillIncrease
    );
    event ProfitDistributed(
        address indexed recipient,
        uint256 amount
    );

    // -----------------------------------------------------------------------
    // Constructor
    // -----------------------------------------------------------------------
    constructor(address admin) ERC20("Nexus Game Theory Token", "NGTT") ERC20Permit("Nexus Game Theory Token") {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(MINTER_ROLE, admin);
        _grantRole(PAUSER_ROLE, admin);
        // Mint genesis supply to admin (treasury will receive its share separately)
        _mint(admin, 100_000_000 * 1e18); // 10 % genesis alloc
    }

    // -----------------------------------------------------------------------
    // Minting (capped)
    // -----------------------------------------------------------------------
    function mint(address to, uint256 amount) external onlyRole(MINTER_ROLE) {
        require(totalSupply() + amount <= MAX_SUPPLY, "NexusToken: cap exceeded");
        _mint(to, amount);
    }

    // -----------------------------------------------------------------------
    // Game reward distribution
    // -----------------------------------------------------------------------
    function distributeGameReward(
        address player,
        uint256 reward,
        uint256 skillIncrease
    ) external onlyRole(GAME_ROLE) {
        require(totalSupply() + reward <= MAX_SUPPLY, "NexusToken: cap exceeded");
        _mint(player, reward);
        emit GameCompleted(player, reward, skillIncrease);
    }

    function distributeProfitSharing(
        address[] calldata recipients,
        uint256[] calldata amounts
    ) external onlyRole(MINTER_ROLE) {
        require(recipients.length == amounts.length, "NexusToken: length mismatch");
        for (uint256 i = 0; i < recipients.length; i++) {
            require(totalSupply() + amounts[i] <= MAX_SUPPLY, "NexusToken: cap exceeded");
            _mint(recipients[i], amounts[i]);
            emit ProfitDistributed(recipients[i], amounts[i]);
        }
    }

    // -----------------------------------------------------------------------
    // Pause
    // -----------------------------------------------------------------------
    function pause()   external onlyRole(PAUSER_ROLE) { _pause(); }
    function unpause() external onlyRole(PAUSER_ROLE) { _unpause(); }

    // -----------------------------------------------------------------------
    // Overrides required by Solidity
    // -----------------------------------------------------------------------
    function _update(address from, address to, uint256 value)
        internal
        override(ERC20, ERC20Votes)
    {
        require(!paused(), "NexusToken: token transfer while paused");
        super._update(from, to, value);
    }

    function nonces(address owner)
        public
        view
        override(ERC20Permit, Nonces)
        returns (uint256)
    {
        return super.nonces(owner);
    }
}
