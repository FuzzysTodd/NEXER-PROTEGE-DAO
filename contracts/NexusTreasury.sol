// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title NexusTreasury
 * @notice Multi-sig DAO treasury for the Nexus Protocol.
 *         ETH and ERC-20 deposits are accepted permissionlessly.
 *         Withdrawals above LARGE_TRANSFER_THRESHOLD require N-of-M guardian
 *         confirmations before execution.
 *
 * Agent assignments:
 *   mcp-fin-012 Withdrawal Placement Scanner — audits placements
 *   mcp-010     Financial Analytics Agent    — tracks revenue flows
 *   nexus-treasury-ops                       — multi-sig protocols
 *
 * @author Nexus Protocol DAO  (nexus-treasury-ops · nexus-security-audit)
 */
contract NexusTreasury is AccessControl, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;

    // -----------------------------------------------------------------------
    // Roles
    // -----------------------------------------------------------------------
    bytes32 public constant GUARDIAN_ROLE  = keccak256("GUARDIAN_ROLE");
    bytes32 public constant EXECUTOR_ROLE  = keccak256("EXECUTOR_ROLE");
    bytes32 public constant PAUSER_ROLE    = keccak256("PAUSER_ROLE");

    // -----------------------------------------------------------------------
    // Parameters
    // -----------------------------------------------------------------------
    uint256 public constant LARGE_TRANSFER_THRESHOLD = 10 ether;
    uint8   public requiredConfirmations;

    // -----------------------------------------------------------------------
    // Large-transfer queue
    // -----------------------------------------------------------------------
    struct PendingTransfer {
        address payable recipient;
        uint256 amount;
        string  reason;
        uint8   confirmations;
        bool    executed;
        mapping(address => bool) confirmed;
    }

    uint256 public nextNonce;
    mapping(uint256 => PendingTransfer) private _pendingTransfers;

    // -----------------------------------------------------------------------
    // Events (mirrored in nexus-signal-bus.js TREASURY_ABI)
    // -----------------------------------------------------------------------
    event ETHDeposited(address indexed sender, uint256 amount);
    event ETHTransferred(address indexed recipient, uint256 amount, string reason);
    event ERC20Deposited(address indexed token, address indexed sender, uint256 amount);
    event ERC20Transferred(address indexed token, address indexed recipient, uint256 amount, string reason);
    event TreasuryPaused(address indexed guardian);
    event TreasuryUnpaused(address indexed guardian);
    event LargeETHTransferRequested(uint256 indexed nonce, address indexed recipient, uint256 amount, address requestedBy);
    event LargeETHTransferConfirmed(uint256 indexed nonce, address indexed confirmedBy);
    event LargeETHTransferExecuted(uint256 indexed nonce, address indexed recipient, uint256 amount);

    // -----------------------------------------------------------------------
    // Constructor
    // -----------------------------------------------------------------------
    constructor(address admin, address[] memory guardians, uint8 _requiredConfirmations) {
        require(_requiredConfirmations > 0 && _requiredConfirmations <= guardians.length,
            "NexusTreasury: invalid confirmations");
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(EXECUTOR_ROLE, admin);
        _grantRole(PAUSER_ROLE, admin);
        for (uint256 i = 0; i < guardians.length; i++) {
            _grantRole(GUARDIAN_ROLE, guardians[i]);
        }
        requiredConfirmations = _requiredConfirmations;
    }

    receive() external payable {
        emit ETHDeposited(msg.sender, msg.value);
    }

    // -----------------------------------------------------------------------
    // ETH transfers
    // -----------------------------------------------------------------------
    function transferETH(
        address payable recipient,
        uint256 amount,
        string calldata reason
    ) external onlyRole(EXECUTOR_ROLE) nonReentrant whenNotPaused {
        require(address(this).balance >= amount, "NexusTreasury: insufficient balance");
        if (amount >= LARGE_TRANSFER_THRESHOLD) {
            uint256 nonce = nextNonce++;
            PendingTransfer storage pt = _pendingTransfers[nonce];
            pt.recipient = recipient;
            pt.amount    = amount;
            pt.reason    = reason;
            emit LargeETHTransferRequested(nonce, recipient, amount, msg.sender);
        } else {
            recipient.transfer(amount);
            emit ETHTransferred(recipient, amount, reason);
        }
    }

    function confirmLargeTransfer(uint256 nonce) external onlyRole(GUARDIAN_ROLE) {
        PendingTransfer storage pt = _pendingTransfers[nonce];
        require(!pt.executed, "NexusTreasury: already executed");
        require(!pt.confirmed[msg.sender], "NexusTreasury: already confirmed");
        pt.confirmed[msg.sender] = true;
        pt.confirmations++;
        emit LargeETHTransferConfirmed(nonce, msg.sender);
        if (pt.confirmations >= requiredConfirmations) {
            pt.executed = true;
            pt.recipient.transfer(pt.amount);
            emit LargeETHTransferExecuted(nonce, pt.recipient, pt.amount);
        }
    }

    // -----------------------------------------------------------------------
    // ERC-20 transfers
    // -----------------------------------------------------------------------
    function depositERC20(address token, uint256 amount) external {
        IERC20(token).safeTransferFrom(msg.sender, address(this), amount);
        emit ERC20Deposited(token, msg.sender, amount);
    }

    function transferERC20(
        address token,
        address recipient,
        uint256 amount,
        string calldata reason
    ) external onlyRole(EXECUTOR_ROLE) nonReentrant whenNotPaused {
        IERC20(token).safeTransfer(recipient, amount);
        emit ERC20Transferred(token, recipient, amount, reason);
    }

    // -----------------------------------------------------------------------
    // Pause
    // -----------------------------------------------------------------------
    function pause()   external onlyRole(PAUSER_ROLE) { _pause();   emit TreasuryPaused(msg.sender); }
    function unpause() external onlyRole(PAUSER_ROLE) { _unpause(); emit TreasuryUnpaused(msg.sender); }

    // -----------------------------------------------------------------------
    // View
    // -----------------------------------------------------------------------
    function ethBalance() external view returns (uint256) { return address(this).balance; }
}
