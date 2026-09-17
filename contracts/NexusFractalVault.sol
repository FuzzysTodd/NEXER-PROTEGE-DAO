// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/extensions/ERC4626.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title NexusFractalVault
 * @notice ERC-4626 auto-compounding vault for NGTT.
 *         - Users deposit NGTT, receive fNGTT shares.
 *         - A keeper (mcp-010 bot) calls `harvestAndReinvest` each cycle to
 *           compound yield back into the vault.
 *         - Depositors redeem shares for proportional underlying at any time.
 *
 * Events match nexus-signal-bus.js FRACTAL_VAULT_ABI exactly.
 *
 * Agent assignments:
 *   mcp-010 Financial Analytics Agent — tracks harvest cycles, APY
 *   nexus-defi-architect              — ERC-4626 vault patterns
 *   nexus-treasury-ops                — stablecoin + yield strategy
 *
 * @author Nexus Protocol DAO  (nexus-defi-architect · nexus-treasury-ops)
 */
contract NexusFractalVault is ERC4626, Ownable, ReentrancyGuard {
    // -----------------------------------------------------------------------
    // Harvest tracking
    // -----------------------------------------------------------------------
    uint256 public currentCycle;
    address public keeper;          // mcp-010 bot address

    // -----------------------------------------------------------------------
    // Events (match signal-bus ABI)
    // -----------------------------------------------------------------------
    event Deposited(address indexed user, uint256 assets, uint256 shares);
    event Redeemed(address indexed user, uint256 shares, uint256 assets);
    event HarvestReinvested(
        uint256 indexed cycle,
        uint256 yieldAmount,
        uint256 reinvestedAmount,
        uint256 newTotalAssets
    );

    // -----------------------------------------------------------------------
    // Constructor
    // -----------------------------------------------------------------------
    constructor(
        address _asset,     // NGTT token address
        address _owner,
        address _keeper
    )
        ERC4626(IERC20(_asset))
        ERC20("Fractal NGTT Vault", "fNGTT")
        Ownable(_owner)
    {
        keeper = _keeper;
    }

    // -----------------------------------------------------------------------
    // ERC-4626 hooks — emit Nexus-branded events
    // -----------------------------------------------------------------------
    function deposit(uint256 assets, address receiver)
        public override nonReentrant returns (uint256 shares)
    {
        shares = super.deposit(assets, receiver);
        emit Deposited(receiver, assets, shares);
    }

    function redeem(uint256 shares, address receiver, address owner_)
        public override nonReentrant returns (uint256 assets)
    {
        assets = super.redeem(shares, receiver, owner_);
        emit Redeemed(owner_, shares, assets);
    }

    // -----------------------------------------------------------------------
    // Harvest & reinvest (called by mcp-010 keeper bot)
    // -----------------------------------------------------------------------
    /**
     * @notice Transfer `yieldAmount` of underlying tokens into the vault
     *         as yield, then record the harvest event for the signal bus.
     * @param yieldAmount The amount of NGTT being added as protocol yield.
     * @param reinvestedAmount Portion of yield that is compounded (≤ yieldAmount).
     */
    function harvestAndReinvest(uint256 yieldAmount, uint256 reinvestedAmount)
        external
        nonReentrant
    {
        require(msg.sender == keeper || msg.sender == owner(), "NexusFractalVault: not keeper");
        require(reinvestedAmount <= yieldAmount, "NexusFractalVault: reinvested > yield");

        // Pull yield tokens from caller into vault (keeper must have approved)
        IERC20(asset()).transferFrom(msg.sender, address(this), yieldAmount);

        currentCycle++;
        emit HarvestReinvested(currentCycle, yieldAmount, reinvestedAmount, totalAssets());
    }

    // -----------------------------------------------------------------------
    // Admin
    // -----------------------------------------------------------------------
    function setKeeper(address newKeeper) external onlyOwner {
        keeper = newKeeper;
    }
}
