// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/// @title NexusOptionsVault
/// @notice ERC-4626-inspired vault that accumulates NGTT deposits and allows the
///         owner (the DAO, via governance) to record premium income from off-chain
///         covered-call sales, distributing that income proportionally to depositors.
///
/// Key design decisions:
///   - Assets (NGTT) are deposited and a share token (vNGTT) is minted.
///   - Premium income is credited via `recordPremiumIncome(amount)`, which
///     increases the vault's `totalAssets()` so each share becomes worth more.
///   - Depositors redeem shares for proportionally more NGTT as premiums accrue.
///   - The vault does NOT automatically execute any on-chain options trades.
///     The DAO executes off-chain covered-call sales and credits premiums here.
///
/// NES: this contract is a Nexus-authored surface governed by the
/// Nexus Encryption Standard as documented in docs/NEXUS_ENCRYPTION_STANDARD.md.
contract NexusOptionsVault is ERC20Permit, Ownable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    // -------------------------------------------------------------------------
    // Immutables
    // -------------------------------------------------------------------------

    /// @notice The underlying asset deposited into the vault (NGTT).
    IERC20 public immutable asset;

    // -------------------------------------------------------------------------
    // State
    // -------------------------------------------------------------------------

    /// @notice Total NGTT deposited by all users (excludes premium income).
    uint256 public totalDeposited;

    /// @notice Total premium income credited by the DAO.
    uint256 public totalPremiumIncome;

    // -------------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------------

    /// @notice Emitted when a user deposits NGTT and receives vault shares.
    event Deposited(address indexed user, uint256 assets, uint256 shares);

    /// @notice Emitted when a user redeems vault shares for NGTT.
    event Redeemed(address indexed user, uint256 shares, uint256 assets);

    /// @notice Emitted when the DAO credits premium income to the vault.
    event PremiumIncomeRecorded(uint256 amount, uint256 newTotalAssets);

    // -------------------------------------------------------------------------
    // Constructor
    // -------------------------------------------------------------------------

    /// @notice Deploys the options vault.
    /// @param _asset Address of the NGTT token used as the underlying asset.
    constructor(address _asset)
        ERC20("Nexus Options Vault Share", "vNGTT")
        ERC20Permit("Nexus Options Vault Share")
    {
        require(_asset != address(0), "NexusOptionsVault: zero asset");
        asset = IERC20(_asset);
    }

    // -------------------------------------------------------------------------
    // Vault accounting
    // -------------------------------------------------------------------------

    /// @notice Returns the total NGTT managed by this vault (deposits + premiums).
    /// @return Total assets in NGTT (18 decimals).
    function totalAssets() public view returns (uint256) {
        return totalDeposited + totalPremiumIncome;
    }

    /// @notice Converts a share amount to the equivalent NGTT asset amount.
    /// @param shares Number of vault shares.
    /// @return assets Equivalent NGTT amount.
    function convertToAssets(uint256 shares) public view returns (uint256 assets) {
        uint256 supply = totalSupply();
        if (supply == 0) return shares;
        return (shares * totalAssets()) / supply;
    }

    /// @notice Converts an NGTT asset amount to the equivalent share amount.
    /// @param assets NGTT amount.
    /// @return shares Equivalent vault shares.
    function convertToShares(uint256 assets) public view returns (uint256 shares) {
        uint256 supply = totalSupply();
        uint256 total = totalAssets();
        if (supply == 0 || total == 0) return assets;
        return (assets * supply) / total;
    }

    // -------------------------------------------------------------------------
    // Deposit / redeem
    // -------------------------------------------------------------------------

    /// @notice Deposits NGTT and mints vault shares proportional to the current NAV.
    /// @param assets Amount of NGTT to deposit (caller must approve first).
    /// @return shares Number of vault shares minted.
    function deposit(uint256 assets) external nonReentrant returns (uint256 shares) {
        require(assets > 0, "NexusOptionsVault: zero assets");
        shares = convertToShares(assets);
        require(shares > 0, "NexusOptionsVault: zero shares computed");

        totalDeposited += assets;
        asset.safeTransferFrom(msg.sender, address(this), assets);
        _mint(msg.sender, shares);

        emit Deposited(msg.sender, assets, shares);
    }

    /// @notice Redeems vault shares and returns the proportional NGTT (plus accrued premiums).
    /// @param shares Number of vault shares to burn.
    /// @return assets Amount of NGTT returned.
    function redeem(uint256 shares) external nonReentrant returns (uint256 assets) {
        require(shares > 0, "NexusOptionsVault: zero shares");
        require(balanceOf(msg.sender) >= shares, "NexusOptionsVault: insufficient shares");

        assets = convertToAssets(shares);
        require(assets > 0, "NexusOptionsVault: zero assets computed");

        // Adjust accounting proportionally.
        uint256 supply = totalSupply();
        uint256 depositPortion = (totalDeposited * shares) / supply;
        uint256 premiumPortion = assets - depositPortion;

        if (depositPortion > totalDeposited) depositPortion = totalDeposited;
        if (premiumPortion > totalPremiumIncome) premiumPortion = totalPremiumIncome;

        totalDeposited -= depositPortion;
        if (premiumPortion > 0) totalPremiumIncome -= premiumPortion;

        _burn(msg.sender, shares);
        asset.safeTransfer(msg.sender, assets);

        emit Redeemed(msg.sender, shares, assets);
    }

    // -------------------------------------------------------------------------
    // Premium income (DAO-only)
    // -------------------------------------------------------------------------

    /// @notice Credits premium income earned from off-chain covered-call sales.
    ///         The DAO must transfer the NGTT (or equivalent) to this contract first,
    ///         then call this function to update the accounting.
    /// @param amount NGTT amount to credit as premium income.
    function recordPremiumIncome(uint256 amount) external onlyOwner nonReentrant {
        require(amount > 0, "NexusOptionsVault: zero amount");
        // Verify the vault actually received the tokens before crediting.
        uint256 actual = asset.balanceOf(address(this));
        uint256 expected = totalDeposited + totalPremiumIncome + amount;
        require(actual >= expected, "NexusOptionsVault: tokens not received");

        totalPremiumIncome += amount;
        emit PremiumIncomeRecorded(amount, totalAssets());
    }
}
