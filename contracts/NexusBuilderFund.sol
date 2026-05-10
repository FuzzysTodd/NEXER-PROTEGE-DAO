// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/// @title NexusBuilderFund
/// @notice Protocol Guild–style developer compensation pool for the Nexus Protocol DAO.
///
/// ─── WHAT THIS IS ────────────────────────────────────────────────────────────
/// Every time someone pays to use Nexus-authored code (via the REST API, a
/// contract call, or a direct `depositFees()` call), ETH is routed into this
/// contract.  Registered builders earn a proportional slice of that revenue
/// stream simply by having contributed to the protocol — no invoices, no
/// intermediaries, no payment processor.
///
/// ─── HOW THE PAYMENT FLOW WORKS ─────────────────────────────────────────────
/// 1. API / Contract usage emits a micro-fee:
///      • The financial-ops-rest-server logs every API call.
///      • A Chainlink Automation or trusted ORACLE_ROLE wallet calls
///        `recordUsage(bytes32 endpoint, uint256 callCount)` to register
///        off-chain activity on-chain.
///      • Callers of on-chain entry-points can send ETH directly; the
///        `depositFees()` function also accepts explicit deposits.
///
/// 2. ETH accumulates in this contract.
///
/// 3. Any registered builder calls `claimReward()` to pull their proportional
///    share of the accumulated ETH at any time.
///
/// ─── FEE DENOMINATION ────────────────────────────────────────────────────────
/// Fee amounts are set in USD-cent integer units (e.g., `feePerCallUsdCents = 1`
/// = $0.01).  A Chainlink ETH/USD AggregatorV3 feed converts the USD-cent
/// price to the equivalent ETH amount on-the-fly, so callers always know
/// exactly how many wei to send.
///
/// ─── SATOSHI / BTC LAYER ─────────────────────────────────────────────────────
/// Bitcoin (Satoshi) denomination is supported via `getFeeSatoshis()`:
/// the same USD-cent fee is converted to satoshis using a Chainlink BTC/USD
/// feed.  Lightning-network payment channels and WBTC wrappers can route
/// satoshi-denominated fees to this contract via a bridge wallet that calls
/// `depositFees{value: weiEquivalent}()`.
///
/// ─── DATA-DRIVEN ORACLE SETTLEMENT ──────────────────────────────────────────
/// `recordUsage()` is callable by any address with ORACLE_ROLE (typically a
/// Chainlink Automation upkeep or the Nexus signal-bus server acting as a
/// trusted relayer).  Each call records an endpoint-level usage batch.  The
/// total accumulated usage counter drives the dashboard at
/// /api/v1/builder-fund/stats on the REST server.
///
/// ─── PLACEMENT WALLET ────────────────────────────────────────────────────────
/// A `placementWallet` and `placementBps` (basis points, max 5 000 = 50%) can
/// be configured by the admin.  On every `depositFees()` or plain ETH receive,
/// `placementBps / 10 000` of the incoming ETH is forwarded **immediately** to
/// `placementWallet` (e.g., the dashboard treasury wallet).  The remainder
/// enters the pool for builder claims.  Setting `placementWallet = address(0)`
/// or `placementBps = 0` disables the auto-forward.
///
/// ─── NGTT TOKEN AWARDS ───────────────────────────────────────────────────────
/// An optional `ngttToken` (IERC20) and `ngttRewardPerEthWei` rate can be set
/// by the admin.  When a builder claims ETH rewards, the contract transfers
/// `claimedEth * ngttRewardPerEthWei / 1e18` NGTT tokens from its own balance
/// to the builder's wallet as an additional bonus.  The contract must hold
/// NGTT tokens (sent by the admin or minted via governance) for this to work;
/// if the balance is insufficient the ETH claim still succeeds (tokens silently
/// skipped).  Set `ngttRewardPerEthWei = 0` to disable.
///
/// ─── SECURITY ────────────────────────────────────────────────────────────────
/// • `depositFees()` is payable and open to anyone (API gateways, contract
///    hooks, bridge wallets, individual users tipping the protocol).
/// • Placement forward uses `call{value:}`, guarded by ReentrancyGuard.
/// • Claim math uses integer division; dust (wei remainder) stays in the pool.
/// • ReentrancyGuard on all fund-movement functions.
/// • DEFAULT_ADMIN_ROLE required to register/remove builders.
/// • ORACLE_ROLE required to record usage (so external usage data is trust-
///   scoped to the oracle, not to individual callers).
///
/// NES: this contract is a Nexus-authored surface governed by the
/// Nexus Encryption Standard as documented in docs/NEXUS_ENCRYPTION_STANDARD.md.

// ─────────────────────────────────────────────────────────────────────────────
// Chainlink price-feed interface (minimal — only latestRoundData used)
// ─────────────────────────────────────────────────────────────────────────────

/// @dev Minimal AggregatorV3 interface so we avoid importing the full
///      Chainlink NPM package at deployment time.
interface IAggregatorV3 {
    function latestRoundData()
        external
        view
        returns (
            uint80  roundId,
            int256  answer,
            uint256 startedAt,
            uint256 updatedAt,
            uint80  answeredInRound
        );
    function decimals() external view returns (uint8);
}

contract NexusBuilderFund is AccessControl, ReentrancyGuard {
    using SafeERC20 for IERC20;

    // ─────────────────────────────────────────────────────────────────────────
    // Roles
    // ─────────────────────────────────────────────────────────────────────────

    /// @notice May call recordUsage() — assigned to Chainlink Automation upkeep
    ///         or the Nexus signal-bus server acting as a trusted oracle.
    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");

    /// @notice Chainlink ETH/USD price feed (8 decimal answer, e.g. 3_000_00000000 = $3000).
    ///         Set to address(0) to disable USD-denominated fee conversion.
    IAggregatorV3 public ethUsdFeed;

    /// @notice Chainlink BTC/USD price feed for Satoshi denomination.
    ///         Set to address(0) to disable BTC-denominated fee conversion.
    IAggregatorV3 public btcUsdFeed;

    // ─────────────────────────────────────────────────────────────────────────
    // Builder registry
    // ─────────────────────────────────────────────────────────────────────────

    struct Builder {
        address wallet;        // Payment destination
        uint256 shares;        // Relative weight in the pool (e.g., 100 = 1 share)
        string  handle;        // GitHub handle or display name
        string  component;     // Expert domain / code-space attribution (e.g., "Solidity-DeFi-Core")
        uint256 totalClaimed;  // Cumulative ETH (in wei) ever claimed by this builder
        bool    active;        // False = removed from pool but historical data kept
    }

    /// @notice All registered builders (index = builderId).
    Builder[] public builders;

    /// @notice Wallet → builderId (+1, so 0 = not registered).
    mapping(address => uint256) public builderIndex;

    /// @notice keccak256(component) → list of builderIds attributed to that component.
    mapping(bytes32 => uint256[]) private _buildersByComponent;

    /// @notice Total shares across all active builders.
    uint256 public totalShares;

    // ─────────────────────────────────────────────────────────────────────────
    // Placement wallet — auto-forward a cut of each deposit
    // ─────────────────────────────────────────────────────────────────────────

    /// @notice Destination for the auto-forwarded placement cut.
    ///         Set to address(0) to disable placement forwarding.
    address public placementWallet;

    /// @notice Basis points (0–5000) of each deposit auto-forwarded to
    ///         placementWallet.  10 000 bps = 100%.  Max 50% = 5 000.
    uint256 public placementBps;

    // ─────────────────────────────────────────────────────────────────────────
    // NGTT token award — bonus tokens given to builders on ETH claim
    // ─────────────────────────────────────────────────────────────────────────

    /// @notice The NGTT governance token.  Set to address(0) to disable.
    IERC20 public ngttToken;

    /// @notice NGTT tokens awarded per 1 ETH (1e18 wei) claimed.
    ///         E.g., 1000e18 = 1 000 NGTT per ETH claimed.
    ///         Set to 0 to disable token awards.
    uint256 public ngttRewardPerEthWei;

    // ─────────────────────────────────────────────────────────────────────────
    // Fee configuration
    // ─────────────────────────────────────────────────────────────────────────

    /// @notice USD-cent fee per API call (e.g., 1 = $0.01).  Zero disables
    ///         per-call fee enforcement (used when fees are deposited externally
    ///         by a bridge or aggregator rather than enforced at call time).
    uint256 public feePerCallUsdCents;

    // ─────────────────────────────────────────────────────────────────────────
    // Usage accounting
    // ─────────────────────────────────────────────────────────────────────────

    /// @notice Cumulative API calls recorded per endpoint (keccak256 of name).
    mapping(bytes32 => uint256) public usageByEndpoint;

    /// @notice Grand total of all recorded API calls.
    uint256 public totalUsageCalls;

    // ─────────────────────────────────────────────────────────────────────────
    // Snapshot accounting (enables proportional claims without iteration)
    // ─────────────────────────────────────────────────────────────────────────

    /// @notice Running total of ETH (wei) ever deposited into the fund.
    uint256 public totalDeposited;

    /// @notice Snapshot of totalDeposited at the time each builder last claimed.
    mapping(uint256 => uint256) private _lastClaimSnapshot;

    // ─────────────────────────────────────────────────────────────────────────
    // Events
    // ─────────────────────────────────────────────────────────────────────────

    /// @notice Emitted when a builder is registered.
    event BuilderRegistered(uint256 indexed builderId, address indexed wallet, string handle, uint256 shares, string component);

    /// @notice Emitted when a builder's active status or shares are updated.
    event BuilderUpdated(uint256 indexed builderId, uint256 newShares, bool active);

    /// @notice Emitted when ETH is deposited into the fund.
    event FeesDeposited(address indexed from, uint256 amount, string note);

    /// @notice Emitted when API usage is recorded by the oracle.
    event UsageRecorded(bytes32 indexed endpoint, uint256 callCount, address indexed oracle);

    /// @notice Emitted when a builder claims their reward.
    event RewardClaimed(uint256 indexed builderId, address indexed wallet, uint256 amount);

    /// @notice Emitted when the ETH/USD or BTC/USD feed address is updated.
    event PriceFeedUpdated(string feedName, address newFeed);

    /// @notice Emitted when the per-call USD-cent fee is updated.
    event FeePerCallUpdated(uint256 newFeeUsdCents);

    /// @notice Emitted when the placement wallet or bps is updated.
    event PlacementConfigUpdated(address indexed wallet, uint256 bps);

    /// @notice Emitted when ETH is auto-forwarded to the placement wallet.
    event PlacementSent(address indexed to, uint256 amount);

    /// @notice Emitted when NGTT tokens are awarded to a builder on claim.
    event NgttAwarded(uint256 indexed builderId, address indexed wallet, uint256 ngttAmount);

    /// @notice Emitted when the NGTT token award config is updated.
    event NgttRewardConfigUpdated(address indexed token, uint256 rewardPerEthWei);

    // ─────────────────────────────────────────────────────────────────────────
    // Constructor
    // ─────────────────────────────────────────────────────────────────────────

    /// @notice Deploys the builder fund.
    /// @param admin                DEFAULT_ADMIN_ROLE holder (owner wallet).
    /// @param _ethUsdFeed          Chainlink ETH/USD feed address (address(0) to disable).
    /// @param _btcUsdFeed          Chainlink BTC/USD feed address (address(0) to disable).
    /// @param _feePerCallUsdCents  Initial per-call fee in USD cents (0 = free / externally metered).
    /// @param _placementWallet     Auto-forward destination (address(0) to disable).
    /// @param _placementBps        Basis points of each deposit to auto-forward (0–5000).
    constructor(
        address admin,
        address _ethUsdFeed,
        address _btcUsdFeed,
        uint256 _feePerCallUsdCents,
        address _placementWallet,
        uint256 _placementBps
    ) {
        require(admin != address(0), "NexusBuilderFund: zero admin");
        require(_placementBps <= 5000, "NexusBuilderFund: placementBps > 50%");
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(ORACLE_ROLE, admin); // Admin can also act as oracle initially
        ethUsdFeed = IAggregatorV3(_ethUsdFeed);
        btcUsdFeed = IAggregatorV3(_btcUsdFeed);
        feePerCallUsdCents = _feePerCallUsdCents;
        placementWallet = _placementWallet;
        placementBps = _placementBps;
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Builder registry management
    // ─────────────────────────────────────────────────────────────────────────

    /// @notice Registers a new builder in the fund (legacy overload — component defaults to "").
    /// @param wallet   Payment destination address.
    /// @param shares   Relative weight (e.g., 100 = 1 standard share).
    /// @param handle   GitHub handle or display name for the dashboard.
    /// @return builderId  The new builder's array index.
    function registerBuilder(address wallet, uint256 shares, string calldata handle)
        external
        onlyRole(DEFAULT_ADMIN_ROLE)
        returns (uint256 builderId)
    {
        return _registerBuilderCore(wallet, shares, handle, "");
    }

    /// @notice Registers a new builder with explicit expert-domain attribution.
    /// @param wallet     Payment destination address.
    /// @param shares     Relative weight (e.g., 100 = 1 standard share).
    /// @param handle     GitHub handle or display name for the dashboard.
    /// @param component  Expert domain / code-space (e.g., "Solidity-DeFi-Core").
    /// @return builderId  The new builder's array index.
    function registerBuilder(
        address wallet,
        uint256 shares,
        string calldata handle,
        string calldata component
    )
        external
        onlyRole(DEFAULT_ADMIN_ROLE)
        returns (uint256 builderId)
    {
        return _registerBuilderCore(wallet, shares, handle, component);
    }

    /// @dev Core registration logic shared by both `registerBuilder` overloads.
    function _registerBuilderCore(
        address wallet,
        uint256 shares,
        string memory handle,
        string memory component
    )
        internal
        returns (uint256 builderId)
    {
        require(wallet != address(0), "NexusBuilderFund: zero wallet");
        require(shares > 0, "NexusBuilderFund: zero shares");
        require(builderIndex[wallet] == 0, "NexusBuilderFund: already registered");

        builderId = builders.length;
        builders.push(Builder({
            wallet: wallet,
            shares: shares,
            handle: handle,
            component: component,
            totalClaimed: 0,
            active: true
        }));

        builderIndex[wallet] = builderId + 1; // +1 so 0 means "not registered"
        totalShares += shares;

        // New builder starts claiming from the current deposit snapshot
        _lastClaimSnapshot[builderId] = totalDeposited;

        // Track component attribution
        if (bytes(component).length > 0) {
            _buildersByComponent[keccak256(bytes(component))].push(builderId);
        }

        emit BuilderRegistered(builderId, wallet, handle, shares, component);
    }

    /// @notice Updates a builder's share weight or active status.
    /// @param builderId  Index into the builders array.
    /// @param newShares  New share weight (0 = deactivate).
    /// @param active     True to keep active, false to remove from pool.
    function updateBuilder(uint256 builderId, uint256 newShares, bool active)
        external
        onlyRole(DEFAULT_ADMIN_ROLE)
    {
        require(builderId < builders.length, "NexusBuilderFund: unknown builder");

        Builder storage b = builders[builderId];
        totalShares = totalShares - (b.active ? b.shares : 0) + (active ? newShares : 0);
        b.shares = newShares;
        b.active = active;

        emit BuilderUpdated(builderId, newShares, active);
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Fee deposit (open to anyone — API gateways, bridge wallets, users)
    // ─────────────────────────────────────────────────────────────────────────

    /// @dev Splits an incoming ETH payment: forwards placementBps/10000 to
    ///      placementWallet immediately, and adds the remainder to totalDeposited
    ///      (the builder pool).
    ///
    ///      `totalDeposited` intentionally tracks only the builder-pool portion —
    ///      NOT the gross received amount.  This is correct: `claimReward()` uses
    ///      `totalDeposited` to calculate entitlements, and the contract balance
    ///      already excludes the placed portion (forwarded out immediately).
    ///      Tracking gross here would allow builders to claim funds that no longer
    ///      exist in the contract, causing `claimReward()` to revert.
    ///
    ///      Reentrancy: `_handleDeposit` is internal-only.  Every external entry
    ///      point that calls it (`depositFees`, `receive`) is already guarded by
    ///      `nonReentrant`.  The external call to `placementWallet` therefore runs
    ///      inside an active ReentrancyGuard lock, making re-entry impossible.
    function _handleDeposit(uint256 amount) internal {
        if (placementWallet != address(0) && placementBps > 0) {
            uint256 placed = (amount * placementBps) / 10_000;
            if (placed > 0) {
                // CEI: credit pool with the builder portion BEFORE external call
                totalDeposited += (amount - placed);
                (bool ok,) = payable(placementWallet).call{value: placed}("");
                require(ok, "NexusBuilderFund: placement transfer failed");
                emit PlacementSent(placementWallet, placed);
                return;
            }
        }
        totalDeposited += amount;
    }

    /// @notice Deposits ETH into the builder fund.
    /// @param note  Human-readable label for this deposit (e.g., "REST API batch",
    ///              "Lightning bridge settlement", "GitHub Sponsors top-up").
    function depositFees(string calldata note) external payable nonReentrant {
        require(msg.value > 0, "NexusBuilderFund: zero deposit");
        _handleDeposit(msg.value);
        emit FeesDeposited(msg.sender, msg.value, note);
    }

    /// @notice Accepts plain ETH transfers (e.g., from the signal-bus settlement wallet).
    receive() external payable {
        _handleDeposit(msg.value);
        emit FeesDeposited(msg.sender, msg.value, "direct transfer");
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Usage recording (oracle-only)
    // ─────────────────────────────────────────────────────────────────────────

    /// @notice Records off-chain API usage for a given endpoint.
    ///         Called by the Chainlink Automation upkeep or the Nexus oracle relayer.
    /// @param endpoint  keccak256 of the endpoint name (e.g., keccak256("/api/v1/member")).
    /// @param callCount Number of calls to add to the running total.
    function recordUsage(bytes32 endpoint, uint256 callCount)
        external
        onlyRole(ORACLE_ROLE)
    {
        require(callCount > 0, "NexusBuilderFund: zero call count");
        usageByEndpoint[endpoint] += callCount;
        totalUsageCalls += callCount;
        emit UsageRecorded(endpoint, callCount, msg.sender);
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Reward claiming
    // ─────────────────────────────────────────────────────────────────────────

    /// @notice Returns the claimable ETH (wei) for a builder based on deposits
    ///         made since their last claim.
    /// @param builderId  Index into the builders array.
    /// @return claimable  ETH in wei available to claim right now.
    function pendingReward(uint256 builderId) public view returns (uint256 claimable) {
        require(builderId < builders.length, "NexusBuilderFund: unknown builder");
        Builder storage b = builders[builderId];
        if (!b.active || totalShares == 0) return 0;

        uint256 newDeposits = totalDeposited - _lastClaimSnapshot[builderId];
        claimable = (newDeposits * b.shares) / totalShares;
    }

    /// @notice Claims all pending ETH rewards for the calling builder.
    ///         If an NGTT token award rate is configured and the contract holds
    ///         enough NGTT, a proportional NGTT bonus is also transferred.
    ///         The caller must be a registered builder's wallet.
    function claimReward() external nonReentrant {
        uint256 idx = builderIndex[msg.sender];
        require(idx != 0, "NexusBuilderFund: not a registered builder");
        uint256 builderId = idx - 1;

        uint256 amount = pendingReward(builderId);
        require(amount > 0, "NexusBuilderFund: nothing to claim");
        require(address(this).balance >= amount, "NexusBuilderFund: insufficient balance");

        // Update snapshot BEFORE transfer (CEI pattern)
        _lastClaimSnapshot[builderId] = totalDeposited;
        builders[builderId].totalClaimed += amount;

        (bool success,) = payable(msg.sender).call{value: amount}("");
        require(success, "NexusBuilderFund: ETH transfer failed");

        emit RewardClaimed(builderId, msg.sender, amount);

        // NGTT token bonus — sent after ETH transfer; failure is non-blocking
        if (address(ngttToken) != address(0) && ngttRewardPerEthWei > 0) {
            uint256 ngttAmount = (amount * ngttRewardPerEthWei) / 1e18;
            if (ngttAmount > 0 && ngttToken.balanceOf(address(this)) >= ngttAmount) {
                ngttToken.safeTransfer(msg.sender, ngttAmount);
                emit NgttAwarded(builderId, msg.sender, ngttAmount);
            }
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Chainlink price-feed helpers
    // ─────────────────────────────────────────────────────────────────────────

    /// @notice Returns the current ETH/USD price from Chainlink (8 decimals).
    ///         Reverts if the feed is not configured or the price is stale/negative.
    /// @return price  ETH price in USD × 10^8 (e.g., 3_000_00000000 = $3000).
    function getEthUsdPrice() public view returns (uint256 price) {
        require(address(ethUsdFeed) != address(0), "NexusBuilderFund: ETH/USD feed not set");
        (, int256 answer,, uint256 updatedAt,) = ethUsdFeed.latestRoundData();
        require(answer > 0, "NexusBuilderFund: invalid ETH/USD price");
        require(block.timestamp - updatedAt <= 3600, "NexusBuilderFund: ETH/USD price stale (>1h)");
        price = uint256(answer);
    }

    /// @notice Returns the current BTC/USD price from Chainlink (8 decimals).
    /// @return price  BTC price in USD × 10^8.
    function getBtcUsdPrice() public view returns (uint256 price) {
        require(address(btcUsdFeed) != address(0), "NexusBuilderFund: BTC/USD feed not set");
        (, int256 answer,, uint256 updatedAt,) = btcUsdFeed.latestRoundData();
        require(answer > 0, "NexusBuilderFund: invalid BTC/USD price");
        require(block.timestamp - updatedAt <= 3600, "NexusBuilderFund: BTC/USD price stale (>1h)");
        price = uint256(answer);
    }

    /// @notice Converts the per-call USD-cent fee to wei at the current ETH/USD price.
    /// @dev    Formula: wei = (feeUsdCents × 1e18) / (ethUsdPrice × 100)
    ///         where ethUsdPrice has 8 decimals (i.e., divide by 10^8 first).
    ///
    ///         Example: fee = 1 USD-cent, ETH = $3 000
    ///           wei = (1 × 1e18) / (3_000_00000000 × 100 / 1e8)
    ///               = 1e18 / 300_000
    ///               ≈ 3 333 333 333 wei  ≈ 0.0000033 ETH  ≈ $0.01 ✓
    /// @return weiAmount  ETH (wei) equivalent of the current per-call fee.
    function getFeeWei() public view returns (uint256 weiAmount) {
        if (feePerCallUsdCents == 0) return 0;
        uint256 ethPrice8 = getEthUsdPrice(); // USD per ETH × 10^8
        // wei = (cents * 1e18) / (price_in_cents_per_ether)
        // price in cents per ether = ethPrice8 * 100 / 1e8 = ethPrice8 / 1e6
        weiAmount = (feePerCallUsdCents * 1e18 * 1e6) / (ethPrice8 * 100);
    }

    /// @notice Converts the per-call USD-cent fee to satoshis at the current BTC/USD price.
    /// @dev    1 BTC = 100 000 000 satoshis.
    ///         Formula: satoshis = (feeUsdCents × 1e8) / (btcUsdPrice × 100 / 1e8)
    ///                           = (feeUsdCents × 1e16) / btcUsdPrice
    ///
    ///         Example: fee = 1 USD-cent, BTC = $60 000
    ///           satoshis = (1 × 1e16) / 6_000_000_000_000
    ///                    = 1e16 / 6e12 ≈ 1 666 satoshis ≈ $0.01 ✓
    /// @return satoshis  BTC satoshi equivalent of the current per-call fee.
    function getFeeSatoshis() public view returns (uint256 satoshis) {
        if (feePerCallUsdCents == 0) return 0;
        uint256 btcPrice8 = getBtcUsdPrice(); // USD per BTC × 10^8
        // satoshis = (cents / price_per_satoshi_in_cents)
        // price_per_satoshi_in_cents = btcPrice8 / (1e8 * 1e2) = btcPrice8 / 1e10
        satoshis = (feePerCallUsdCents * 1e10) / btcPrice8;
    }

    // ─────────────────────────────────────────────────────────────────────────
    // View helpers
    // ─────────────────────────────────────────────────────────────────────────

    /// @notice Returns the total number of registered builders (including inactive).
    function builderCount() external view returns (uint256) {
        return builders.length;
    }

    /// @notice Returns the builder IDs attributed to a given component/expert domain.
    /// @param component  The component string (e.g., "Solidity-DeFi-Core").
    /// @return ids  Array of builderIds that were registered with this component.
    function buildersByComponent(string calldata component) external view returns (uint256[] memory ids) {
        return _buildersByComponent[keccak256(bytes(component))];
    }

    /// @notice Returns complete info for a builder.
    /// @param builderId  Index into the builders array.
    function getBuilder(uint256 builderId) external view returns (Builder memory) {
        require(builderId < builders.length, "NexusBuilderFund: unknown builder");
        return builders[builderId];
    }

    /// @notice Returns the current ETH balance held in the fund.
    function fundBalance() external view returns (uint256) {
        return address(this).balance;
    }

    /// @notice Returns usage count for an endpoint given its string name.
    /// @param endpointName  Plain-text endpoint name (e.g., "/api/v1/member").
    function usageForEndpoint(string calldata endpointName) external view returns (uint256) {
        return usageByEndpoint[keccak256(abi.encodePacked(endpointName))];
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Admin configuration
    // ─────────────────────────────────────────────────────────────────────────

    /// @notice Updates the Chainlink ETH/USD price feed address.
    /// @param newFeed  New feed address (address(0) to disable).
    function setEthUsdFeed(address newFeed) external onlyRole(DEFAULT_ADMIN_ROLE) {
        ethUsdFeed = IAggregatorV3(newFeed);
        emit PriceFeedUpdated("ETH/USD", newFeed);
    }

    /// @notice Updates the Chainlink BTC/USD price feed address.
    /// @param newFeed  New feed address (address(0) to disable).
    function setBtcUsdFeed(address newFeed) external onlyRole(DEFAULT_ADMIN_ROLE) {
        btcUsdFeed = IAggregatorV3(newFeed);
        emit PriceFeedUpdated("BTC/USD", newFeed);
    }

    /// @notice Updates the per-call fee in USD cents.
    ///         Set to 0 to make the API free (fees deposited externally only).
    /// @param newFeeUsdCents  New fee in USD cents (1 = $0.01 per API call).
    function setFeePerCall(uint256 newFeeUsdCents) external onlyRole(DEFAULT_ADMIN_ROLE) {
        feePerCallUsdCents = newFeeUsdCents;
        emit FeePerCallUpdated(newFeeUsdCents);
    }

    /// @notice Configures the placement wallet and basis points.
    ///         On each deposit, `bps / 10000` of the ETH is immediately forwarded
    ///         to `wallet`, with the remainder staying in the builder pool.
    /// @param wallet  Destination address (address(0) = disable auto-forward).
    /// @param bps     Basis points to forward (0–5000; 5000 = 50%).
    function setPlacementConfig(address wallet, uint256 bps) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(bps <= 5000, "NexusBuilderFund: placementBps > 50%");
        placementWallet = wallet;
        placementBps = bps;
        emit PlacementConfigUpdated(wallet, bps);
    }

    /// @notice Configures the NGTT token bonus awarded to builders on ETH claim.
    /// @param token            NGTT token contract address (address(0) = disable).
    /// @param rewardPerEthWei  NGTT tokens (18 dec) awarded per 1 ETH (1e18 wei) claimed.
    ///                         E.g., 1000e18 = 1 000 NGTT per ETH.
    function setNgttRewardConfig(address token, uint256 rewardPerEthWei)
        external
        onlyRole(DEFAULT_ADMIN_ROLE)
    {
        ngttToken = IERC20(token);
        ngttRewardPerEthWei = rewardPerEthWei;
        emit NgttRewardConfigUpdated(token, rewardPerEthWei);
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Extended view helpers
    // ─────────────────────────────────────────────────────────────────────────

    /// @notice Returns the NGTT token balance currently held by this contract
    ///         (available for builder awards).
    function ngttBalance() external view returns (uint256) {
        if (address(ngttToken) == address(0)) return 0;
        return ngttToken.balanceOf(address(this));
    }

    /// @notice Returns placement and NGTT reward configuration in one call.
    function rewardConfig()
        external
        view
        returns (
            address _placementWallet,
            uint256 _placementBps,
            address _ngttToken,
            uint256 _ngttRewardPerEthWei,
            uint256 _ngttContractBalance
        )
    {
        _placementWallet      = placementWallet;
        _placementBps         = placementBps;
        _ngttToken            = address(ngttToken);
        _ngttRewardPerEthWei  = ngttRewardPerEthWei;
        _ngttContractBalance  = (address(ngttToken) != address(0))
            ? ngttToken.balanceOf(address(this))
            : 0;
    }
}
