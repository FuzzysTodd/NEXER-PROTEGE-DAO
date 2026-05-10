// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/// @title NexusFractalVault
/// @notice ERC-4626-inspired compounding vault that recursively reinvests yield
///         back into the underlying strategy at every harvest cycle.
///
/// Fractal compounding model:
///   - Depositors receive fNGTT shares at the current net-asset-value (NAV).
///   - The owner (DAO) calls harvestAndReinvest() periodically to credit newly
///     earned yield back into totalAssets, increasing the share price.
///   - Because the reinvested amount itself earns future yield, growth is
///     compound (not linear) — approaching fractal compounding as the harvest
///     interval shrinks toward zero.
///   - Kelly-criterion-informed position: the vault never reinvests more than
///     MAX_REINVEST_BPS (10 000 bps = 100%) of a single harvest, allowing the
///     DAO to cap risk per cycle.
///
/// NES: this contract is a Nexus-authored surface governed by the
/// Nexus Encryption Standard as documented in docs/NEXUS_ENCRYPTION_STANDARD.md.
contract NexusFractalVault is ERC20Permit, Ownable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    // -------------------------------------------------------------------------
    // Immutables
    // -------------------------------------------------------------------------

    /// @notice The underlying yield-bearing asset (NGTT).
    IERC20 public immutable asset;

    // -------------------------------------------------------------------------
    // State
    // -------------------------------------------------------------------------

    /// @notice Total NGTT deposited by all users (base principal).
    uint256 public totalPrincipal;

    /// @notice Cumulative yield reinvested into the vault (compounds over time).
    uint256 public totalReinvested;

    /// @notice Number of completed harvest cycles.
    uint256 public harvestCount;

    /// @notice Maximum reinvestment fraction per harvest cycle, in basis points.
    ///         10 000 bps = 100 % (reinvest all harvested yield). Updatable by owner.
    uint256 public maxReinvestBps = 10_000;

    // -------------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------------

    /// @notice Emitted when a user deposits NGTT.
    event Deposited(address indexed user, uint256 assets, uint256 shares);

    /// @notice Emitted when a user redeems fNGTT shares.
    event Redeemed(address indexed user, uint256 shares, uint256 assets);

    /// @notice Emitted each harvest cycle.
    event HarvestReinvested(
        uint256 indexed cycle,
        uint256 yieldAmount,
        uint256 reinvestedAmount,
        uint256 newTotalAssets
    );

    /// @notice Emitted when the max reinvestment fraction is updated.
    event MaxReinvestBpsUpdated(uint256 newBps);

    // -------------------------------------------------------------------------
    // Constructor
    // -------------------------------------------------------------------------

    /// @notice Deploys the fractal vault.
    /// @param _asset Address of the NGTT token.
    constructor(address _asset)
        ERC20("Nexus Fractal Vault Share", "fNGTT")
        ERC20Permit("Nexus Fractal Vault Share")
    {
        require(_asset != address(0), "NexusFractalVault: zero asset");
        asset = IERC20(_asset);
    }

    // -------------------------------------------------------------------------
    // Vault accounting
    // -------------------------------------------------------------------------

    /// @notice Total NGTT managed by the vault (principal + all reinvested yield).
    /// @return Total assets in NGTT.
    function totalAssets() public view returns (uint256) {
        return totalPrincipal + totalReinvested;
    }

    /// @notice Converts shares to the underlying NGTT amount at current NAV.
    /// @param shares Number of fNGTT shares.
    /// @return assets Equivalent NGTT.
    function convertToAssets(uint256 shares) public view returns (uint256 assets) {
        uint256 supply = totalSupply();
        if (supply == 0) return shares;
        return (shares * totalAssets()) / supply;
    }

    /// @notice Converts NGTT amount to shares at current NAV.
    /// @param assets NGTT amount.
    /// @return shares Equivalent fNGTT shares.
    function convertToShares(uint256 assets) public view returns (uint256 shares) {
        uint256 supply = totalSupply();
        uint256 total = totalAssets();
        if (supply == 0 || total == 0) return assets;
        return (assets * supply) / total;
    }

    // -------------------------------------------------------------------------
    // Deposit / redeem
    // -------------------------------------------------------------------------

    /// @notice Deposits NGTT and mints fNGTT shares at current NAV.
    /// @param assets Amount of NGTT to deposit (caller must approve first).
    /// @return shares Vault shares minted.
    function deposit(uint256 assets) external nonReentrant returns (uint256 shares) {
        require(assets > 0, "NexusFractalVault: zero assets");
        shares = convertToShares(assets);
        require(shares > 0, "NexusFractalVault: zero shares computed");

        totalPrincipal += assets;
        asset.safeTransferFrom(msg.sender, address(this), assets);
        _mint(msg.sender, shares);

        emit Deposited(msg.sender, assets, shares);
    }

    /// @notice Redeems fNGTT shares for proportional NGTT (principal + compound yield).
    /// @param shares fNGTT shares to burn.
    /// @return assets NGTT returned.
    function redeem(uint256 shares) external nonReentrant returns (uint256 assets) {
        require(shares > 0, "NexusFractalVault: zero shares");
        require(balanceOf(msg.sender) >= shares, "NexusFractalVault: insufficient shares");

        assets = convertToAssets(shares);
        require(assets > 0, "NexusFractalVault: zero assets computed");

        // Reduce principal and reinvested proportionally.
        uint256 supply = totalSupply();
        uint256 principalPortion = (totalPrincipal * shares) / supply;
        uint256 reinvestedPortion = assets - principalPortion;

        if (principalPortion > totalPrincipal) principalPortion = totalPrincipal;
        if (reinvestedPortion > totalReinvested) reinvestedPortion = totalReinvested;

        totalPrincipal -= principalPortion;
        if (reinvestedPortion > 0) totalReinvested -= reinvestedPortion;

        _burn(msg.sender, shares);
        asset.safeTransfer(msg.sender, assets);

        emit Redeemed(msg.sender, shares, assets);
    }

    // -------------------------------------------------------------------------
    // Harvest and reinvest (DAO-only)
    // -------------------------------------------------------------------------

    /// @notice Credits a yield harvest and immediately reinvests it into the vault.
    ///         The DAO transfers the harvested NGTT to this contract, then calls
    ///         this function.  The reinvested amount increases totalAssets, making
    ///         each share worth more on the next NAV calculation.
    ///
    /// @param yieldAmount Total yield harvested in this cycle (NGTT, 18 decimals).
    /// @param reinvestBps  Fraction of yieldAmount to reinvest in basis points.
    ///                     Must be ≤ maxReinvestBps.  The remainder stays in the vault
    ///                     as a fee buffer (redeemable by the DAO via governance).
    function harvestAndReinvest(uint256 yieldAmount, uint256 reinvestBps)
        external
        onlyOwner
        nonReentrant
    {
        require(yieldAmount > 0, "NexusFractalVault: zero yield");
        require(reinvestBps <= maxReinvestBps, "NexusFractalVault: reinvestBps too high");

        // Verify the tokens were actually transferred to this contract.
        uint256 balance = asset.balanceOf(address(this));
        require(
            balance >= totalAssets() + yieldAmount,
            "NexusFractalVault: yield tokens not received"
        );

        uint256 toReinvest = (yieldAmount * reinvestBps) / 10_000;
        totalReinvested += toReinvest;
        // Any remaining yield (yieldAmount - toReinvest) stays in the contract
        // balance as a DAO fee buffer, redeemable only via governance.

        harvestCount++;
        emit HarvestReinvested(harvestCount, yieldAmount, toReinvest, totalAssets());
    }

    // -------------------------------------------------------------------------
    // Owner configuration
    // -------------------------------------------------------------------------

    /// @notice Updates the maximum reinvestment fraction.
    /// @param newBps New ceiling in basis points (1–10 000).
    function setMaxReinvestBps(uint256 newBps) external onlyOwner {
        require(newBps >= 1 && newBps <= 10_000, "NexusFractalVault: bps out of range");
        maxReinvestBps = newBps;
        emit MaxReinvestBpsUpdated(newBps);
    }

    // -------------------------------------------------------------------------
    // View helpers
    // -------------------------------------------------------------------------

    /// @notice Estimates the compound growth factor after N harvest cycles
    ///         at a fixed per-cycle yield rate r (expressed in basis points).
    ///         Implements the standard compound formula: (1 + r)^N.
    ///         Uses integer math with 1e18 precision.
    /// @param ratePerCycleBps Per-cycle yield rate in basis points (e.g. 100 = 1 %).
    /// @param cycles          Number of compounding cycles.
    /// @return growthFactor18 Growth factor scaled by 1e18 (1e18 = 1×, 2e18 = 2×).
    function estimateCompoundGrowth(uint256 ratePerCycleBps, uint256 cycles)
        external
        pure
        returns (uint256 growthFactor18)
    {
        uint256 factor = 1e18; // Start at 1.0 (scaled)
        uint256 rateScaled = 1e18 + (ratePerCycleBps * 1e14); // (1 + r) scaled
        for (uint256 i = 0; i < cycles; i++) {
            factor = (factor * rateScaled) / 1e18;
        }
        return factor;
    }
}
