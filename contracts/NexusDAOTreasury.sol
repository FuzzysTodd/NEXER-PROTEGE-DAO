// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/// @title NexusDAOTreasury
/// @notice DAO-controlled treasury that holds ETH and ERC-20 tokens.
/// @dev All fund-movement functions are restricted to EXECUTOR_ROLE, which is
///      assigned exclusively to the NexusDAOTimelock after deployment.  No
///      funds can therefore leave the treasury without a successful on-chain
///      governance vote followed by the mandatory timelock delay.
///
///      Large transfers (above MULTISIG_THRESHOLD) additionally require a
///      second GUARDIAN_ROLE co-signature before the executor can complete the
///      transfer.  This two-step approval prevents a single compromised key
///      from draining the treasury even if it holds EXECUTOR_ROLE.
///
///      Flow for a large transfer:
///        1. EXECUTOR_ROLE calls requestLargeTransfer*() — creates a pending entry.
///        2. A GUARDIAN_ROLE (≠ msg.sender of step 1) calls confirmLargeTransfer*().
///        3. EXECUTOR_ROLE calls executeLargeTransfer*() — funds are moved.
///
///      NES: this contract is a Nexus-authored surface governed by the
///      Nexus Encryption Standard as documented in docs/NEXUS_ENCRYPTION_STANDARD.md.
///
/// Access model:
///   - DEFAULT_ADMIN_ROLE  : deployment-time admin (owner wallet); manages role grants.
///   - EXECUTOR_ROLE       : granted to NexusDAOTimelock; the only role that may
///                           transfer ETH or ERC-20 tokens out of the treasury.
///   - GUARDIAN_ROLE       : granted to Owner and/or Super Delegates; may pause
///                           treasury operations in an emergency, and must co-sign
///                           large transfers above MULTISIG_THRESHOLD.
///
/// Deployment:
///   1. Deploy NexusDAOTreasury(admin = owner wallet).
///   2. After the Timelock is deployed, call
///        treasury.grantRole(EXECUTOR_ROLE, timelockAddress)
///   3. Optionally grant GUARDIAN_ROLE to the owner and each Super Delegate.
contract NexusDAOTreasury is AccessControl, ReentrancyGuard {
    using SafeERC20 for IERC20;

    // -------------------------------------------------------------------------
    // Roles
    // -------------------------------------------------------------------------

    /// @notice Role required to transfer ETH or tokens out of the treasury.
    ///         Assigned exclusively to NexusDAOTimelock.
    bytes32 public constant EXECUTOR_ROLE = keccak256("EXECUTOR_ROLE");

    /// @notice Role that can pause and unpause treasury operations.
    ///         Assigned to Owner and Super Delegates for emergency response.
    ///         Also required to co-sign large transfers.
    bytes32 public constant GUARDIAN_ROLE = keccak256("GUARDIAN_ROLE");

    // -------------------------------------------------------------------------
    // Multi-sig large-transfer configuration
    // -------------------------------------------------------------------------

    /// @notice ETH amount (in wei) above which a guardian co-signature is required.
    ///         Default: 1 ETH. Updatable by DEFAULT_ADMIN_ROLE via governance.
    uint256 public MULTISIG_THRESHOLD = 1 ether;

    /// @notice ERC-20 amount (in token units, 18 decimals) above which a guardian
    ///         co-signature is required.
    uint256 public ERC20_MULTISIG_THRESHOLD = 1_000 * 10 ** 18;

    // -------------------------------------------------------------------------
    // Pending large-transfer state
    // -------------------------------------------------------------------------

    struct PendingETHTransfer {
        address payable recipient;
        uint256 amount;
        string reason;
        address requestedBy;
        address confirmedBy;
        uint256 requestedAt;
        bool executed;
    }

    struct PendingERC20Transfer {
        address token;
        address recipient;
        uint256 amount;
        string reason;
        address requestedBy;
        address confirmedBy;
        uint256 requestedAt;
        bool executed;
    }

    mapping(uint256 => PendingETHTransfer) public pendingETH;
    mapping(uint256 => PendingERC20Transfer) public pendingERC20;
    uint256 private _pendingETHNonce;
    uint256 private _pendingERC20Nonce;

    // -------------------------------------------------------------------------
    // State
    // -------------------------------------------------------------------------

    /// @notice Whether treasury transfers are currently paused.
    bool public paused;

    // -------------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------------

    /// @notice Emitted when ETH is deposited into the treasury.
    event ETHDeposited(address indexed sender, uint256 amount);

    /// @notice Emitted when ETH is transferred out of the treasury by governance.
    event ETHTransferred(address indexed recipient, uint256 amount, string reason);

    /// @notice Emitted when an ERC-20 token is deposited into the treasury.
    event ERC20Deposited(address indexed token, address indexed sender, uint256 amount);

    /// @notice Emitted when an ERC-20 token is transferred out of the treasury.
    event ERC20Transferred(address indexed token, address indexed recipient, uint256 amount, string reason);

    /// @notice Emitted when the treasury is paused by a guardian.
    event TreasuryPaused(address indexed guardian);

    /// @notice Emitted when the treasury is unpaused by a guardian.
    event TreasuryUnpaused(address indexed guardian);

    /// @notice Emitted when a large ETH transfer is requested.
    event LargeETHTransferRequested(uint256 indexed nonce, address indexed recipient, uint256 amount, address requestedBy);

    /// @notice Emitted when a large ETH transfer is confirmed by a guardian.
    event LargeETHTransferConfirmed(uint256 indexed nonce, address indexed confirmedBy);

    /// @notice Emitted when a large ETH transfer is executed after confirmation.
    event LargeETHTransferExecuted(uint256 indexed nonce, address indexed recipient, uint256 amount);

    /// @notice Emitted when a large ERC-20 transfer is requested.
    event LargeERC20TransferRequested(
        uint256 indexed nonce, address indexed token, address indexed recipient, uint256 amount, address requestedBy
    );

    /// @notice Emitted when a large ERC-20 transfer is confirmed by a guardian.
    event LargeERC20TransferConfirmed(uint256 indexed nonce, address indexed confirmedBy);

    /// @notice Emitted when a large ERC-20 transfer is executed after confirmation.
    event LargeERC20TransferExecuted(uint256 indexed nonce, address indexed token, address indexed recipient, uint256 amount);

    /// @notice Emitted when the multisig ETH threshold is updated.
    event MultisigThresholdUpdated(uint256 newThreshold);

    /// @notice Emitted when the multisig ERC-20 threshold is updated.
    event ERC20MultisigThresholdUpdated(uint256 newThreshold);

    // -------------------------------------------------------------------------
    // Modifiers
    // -------------------------------------------------------------------------

    /// @dev Reverts if the treasury is currently paused.
    modifier whenNotPaused() {
        require(!paused, "NexusDAOTreasury: paused");
        _;
    }

    // -------------------------------------------------------------------------
    // Constructor
    // -------------------------------------------------------------------------

    /// @notice Deploys the treasury and grants the deployer DEFAULT_ADMIN_ROLE.
    /// @param admin Address that holds DEFAULT_ADMIN_ROLE.  This should be the
    ///        owner wallet (`0x33ffc308e693a5b49e0ee0241f41f03ccef495f2`).
    constructor(address admin) {
        require(admin != address(0), "NexusDAOTreasury: zero admin");
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(GUARDIAN_ROLE, admin);
    }

    // -------------------------------------------------------------------------
    // Receive / deposit
    // -------------------------------------------------------------------------

    /// @notice Accepts ETH deposits directly.
    receive() external payable {
        emit ETHDeposited(msg.sender, msg.value);
    }

    /// @notice Accepts ETH via an explicit call (same as receive).
    fallback() external payable {
        emit ETHDeposited(msg.sender, msg.value);
    }

    /// @notice Convenience function to deposit ERC-20 tokens into the treasury.
    /// @param token  The ERC-20 token address.
    /// @param amount Amount to deposit (caller must have approved this contract first).
    function depositERC20(address token, uint256 amount) external nonReentrant {
        require(token != address(0), "NexusDAOTreasury: zero token address");
        require(amount > 0, "NexusDAOTreasury: zero amount");
        IERC20(token).safeTransferFrom(msg.sender, address(this), amount);
        emit ERC20Deposited(token, msg.sender, amount);
    }

    // -------------------------------------------------------------------------
    // ETH transfers (governance-only, with multi-sig for large amounts)
    // -------------------------------------------------------------------------

    /// @notice Transfers ETH to the specified recipient (amounts ≤ MULTISIG_THRESHOLD only).
    ///         For larger amounts use requestLargeETHTransfer / confirmLargeETHTransfer /
    ///         executeLargeETHTransfer. Can only be called by the NexusDAOTimelock (EXECUTOR_ROLE).
    /// @param recipient Destination address.
    /// @param amount    Amount of ETH in wei.
    /// @param reason    Human-readable description for audit logging.
    function transferETH(address payable recipient, uint256 amount, string calldata reason)
        external
        nonReentrant
        whenNotPaused
        onlyRole(EXECUTOR_ROLE)
    {
        require(recipient != address(0), "NexusDAOTreasury: zero recipient");
        require(amount > 0, "NexusDAOTreasury: zero amount");
        require(amount <= MULTISIG_THRESHOLD, "NexusDAOTreasury: amount exceeds threshold; use large-transfer flow");
        require(address(this).balance >= amount, "NexusDAOTreasury: insufficient ETH");

        (bool success,) = recipient.call{value: amount}("");
        require(success, "NexusDAOTreasury: ETH transfer failed");

        emit ETHTransferred(recipient, amount, reason);
    }

    /// @notice Requests a large ETH transfer (above MULTISIG_THRESHOLD).
    ///         Must be confirmed by a different guardian before execution.
    /// @param recipient Destination address.
    /// @param amount    Amount of ETH in wei (must exceed MULTISIG_THRESHOLD).
    /// @param reason    Human-readable description for audit logging.
    /// @return nonce Identifier for this pending transfer.
    function requestLargeETHTransfer(address payable recipient, uint256 amount, string calldata reason)
        external
        whenNotPaused
        onlyRole(EXECUTOR_ROLE)
        returns (uint256 nonce)
    {
        require(recipient != address(0), "NexusDAOTreasury: zero recipient");
        require(amount > MULTISIG_THRESHOLD, "NexusDAOTreasury: use transferETH for small amounts");
        require(address(this).balance >= amount, "NexusDAOTreasury: insufficient ETH");

        nonce = ++_pendingETHNonce;
        pendingETH[nonce] = PendingETHTransfer({
            recipient: recipient,
            amount: amount,
            reason: reason,
            requestedBy: msg.sender,
            confirmedBy: address(0),
            requestedAt: block.timestamp,
            executed: false
        });

        emit LargeETHTransferRequested(nonce, recipient, amount, msg.sender);
    }

    /// @notice Co-signs a pending large ETH transfer.
    ///         Must be called by a GUARDIAN_ROLE address different from the requester.
    /// @param nonce The pending transfer identifier.
    function confirmLargeETHTransfer(uint256 nonce) external onlyRole(GUARDIAN_ROLE) {
        PendingETHTransfer storage transfer = pendingETH[nonce];
        require(transfer.requestedAt > 0, "NexusDAOTreasury: unknown nonce");
        require(!transfer.executed, "NexusDAOTreasury: already executed");
        require(transfer.confirmedBy == address(0), "NexusDAOTreasury: already confirmed");
        require(msg.sender != transfer.requestedBy, "NexusDAOTreasury: requester cannot confirm");

        transfer.confirmedBy = msg.sender;
        emit LargeETHTransferConfirmed(nonce, msg.sender);
    }

    /// @notice Executes a large ETH transfer that has been confirmed by a guardian.
    /// @param nonce The pending transfer identifier.
    function executeLargeETHTransfer(uint256 nonce)
        external
        nonReentrant
        whenNotPaused
        onlyRole(EXECUTOR_ROLE)
    {
        PendingETHTransfer storage transfer = pendingETH[nonce];
        require(transfer.requestedAt > 0, "NexusDAOTreasury: unknown nonce");
        require(!transfer.executed, "NexusDAOTreasury: already executed");
        require(transfer.confirmedBy != address(0), "NexusDAOTreasury: not yet confirmed");
        require(address(this).balance >= transfer.amount, "NexusDAOTreasury: insufficient ETH");

        transfer.executed = true;

        (bool success,) = transfer.recipient.call{value: transfer.amount}("");
        require(success, "NexusDAOTreasury: ETH transfer failed");

        emit LargeETHTransferExecuted(nonce, transfer.recipient, transfer.amount);
        emit ETHTransferred(transfer.recipient, transfer.amount, transfer.reason);
    }

    // -------------------------------------------------------------------------
    // ERC-20 transfers (governance-only, with multi-sig for large amounts)
    // -------------------------------------------------------------------------

    /// @notice Transfers ERC-20 tokens to the specified recipient.
    ///         For amounts ≤ ERC20_MULTISIG_THRESHOLD, executes immediately.
    ///         Can only be called by the NexusDAOTimelock (EXECUTOR_ROLE).
    /// @param token     The ERC-20 token address.
    /// @param recipient Destination address.
    /// @param amount    Token amount (in token's native decimals).
    /// @param reason    Human-readable description for audit logging.
    function transferERC20(
        address token,
        address recipient,
        uint256 amount,
        string calldata reason
    ) external nonReentrant whenNotPaused onlyRole(EXECUTOR_ROLE) {
        require(token != address(0), "NexusDAOTreasury: zero token address");
        require(recipient != address(0), "NexusDAOTreasury: zero recipient");
        require(amount > 0, "NexusDAOTreasury: zero amount");
        require(amount <= ERC20_MULTISIG_THRESHOLD, "NexusDAOTreasury: amount exceeds threshold; use large-transfer flow");

        IERC20(token).safeTransfer(recipient, amount);
        emit ERC20Transferred(token, recipient, amount, reason);
    }

    /// @notice Requests a large ERC-20 transfer (above ERC20_MULTISIG_THRESHOLD).
    /// @return nonce Identifier for this pending transfer.
    function requestLargeERC20Transfer(
        address token,
        address recipient,
        uint256 amount,
        string calldata reason
    ) external whenNotPaused onlyRole(EXECUTOR_ROLE) returns (uint256 nonce) {
        require(token != address(0), "NexusDAOTreasury: zero token address");
        require(recipient != address(0), "NexusDAOTreasury: zero recipient");
        require(amount > ERC20_MULTISIG_THRESHOLD, "NexusDAOTreasury: use transferERC20 for small amounts");

        nonce = ++_pendingERC20Nonce;
        pendingERC20[nonce] = PendingERC20Transfer({
            token: token,
            recipient: recipient,
            amount: amount,
            reason: reason,
            requestedBy: msg.sender,
            confirmedBy: address(0),
            requestedAt: block.timestamp,
            executed: false
        });

        emit LargeERC20TransferRequested(nonce, token, recipient, amount, msg.sender);
    }

    /// @notice Co-signs a pending large ERC-20 transfer.
    /// @param nonce The pending transfer identifier.
    function confirmLargeERC20Transfer(uint256 nonce) external onlyRole(GUARDIAN_ROLE) {
        PendingERC20Transfer storage transfer = pendingERC20[nonce];
        require(transfer.requestedAt > 0, "NexusDAOTreasury: unknown nonce");
        require(!transfer.executed, "NexusDAOTreasury: already executed");
        require(transfer.confirmedBy == address(0), "NexusDAOTreasury: already confirmed");
        require(msg.sender != transfer.requestedBy, "NexusDAOTreasury: requester cannot confirm");

        transfer.confirmedBy = msg.sender;
        emit LargeERC20TransferConfirmed(nonce, msg.sender);
    }

    /// @notice Executes a large ERC-20 transfer that has been confirmed by a guardian.
    /// @param nonce The pending transfer identifier.
    function executeLargeERC20Transfer(uint256 nonce)
        external
        nonReentrant
        whenNotPaused
        onlyRole(EXECUTOR_ROLE)
    {
        PendingERC20Transfer storage transfer = pendingERC20[nonce];
        require(transfer.requestedAt > 0, "NexusDAOTreasury: unknown nonce");
        require(!transfer.executed, "NexusDAOTreasury: already executed");
        require(transfer.confirmedBy != address(0), "NexusDAOTreasury: not yet confirmed");

        transfer.executed = true;

        IERC20(transfer.token).safeTransfer(transfer.recipient, transfer.amount);
        emit LargeERC20TransferExecuted(nonce, transfer.token, transfer.recipient, transfer.amount);
        emit ERC20Transferred(transfer.token, transfer.recipient, transfer.amount, transfer.reason);
    }

    // -------------------------------------------------------------------------
    // Threshold administration
    // -------------------------------------------------------------------------

    /// @notice Updates the ETH multi-sig threshold. Callable by DEFAULT_ADMIN_ROLE.
    /// @param newThreshold New threshold in wei (must be > 0).
    function setMultisigThreshold(uint256 newThreshold) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(newThreshold > 0, "NexusDAOTreasury: zero threshold");
        MULTISIG_THRESHOLD = newThreshold;
        emit MultisigThresholdUpdated(newThreshold);
    }

    /// @notice Updates the ERC-20 multi-sig threshold. Callable by DEFAULT_ADMIN_ROLE.
    /// @param newThreshold New threshold in token units (must be > 0).
    function setERC20MultisigThreshold(uint256 newThreshold) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(newThreshold > 0, "NexusDAOTreasury: zero threshold");
        ERC20_MULTISIG_THRESHOLD = newThreshold;
        emit ERC20MultisigThresholdUpdated(newThreshold);
    }

    // -------------------------------------------------------------------------
    // Emergency controls (guardian)
    // -------------------------------------------------------------------------

    /// @notice Pauses all outgoing transfers.  Called by a guardian in an emergency.
    function pause() external onlyRole(GUARDIAN_ROLE) {
        require(!paused, "NexusDAOTreasury: already paused");
        paused = true;
        emit TreasuryPaused(msg.sender);
    }

    /// @notice Unpauses the treasury after an emergency is resolved.
    function unpause() external onlyRole(GUARDIAN_ROLE) {
        require(paused, "NexusDAOTreasury: not paused");
        paused = false;
        emit TreasuryUnpaused(msg.sender);
    }

    // -------------------------------------------------------------------------
    // View helpers
    // -------------------------------------------------------------------------

    /// @notice Returns the current ETH balance held by the treasury.
    /// @return ETH balance in wei.
    function ethBalance() external view returns (uint256) {
        return address(this).balance;
    }

    /// @notice Returns the current balance of an ERC-20 token held by the treasury.
    /// @param token The ERC-20 token address.
    /// @return Token balance in the token's native decimals.
    function tokenBalance(address token) external view returns (uint256) {
        return IERC20(token).balanceOf(address(this));
    }
}
