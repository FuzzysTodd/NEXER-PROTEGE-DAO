# Nexus Builder Fund — Developer Micropayment Protocol

## What it is

The **NexusBuilderFund** is a data-driven, on-chain developer compensation pool.
It answers the question:

> *"Can we sparsely embed a payment API in the code so that every time someone
> uses the protocol, a tiny satoshi/wei fee flows automatically to the builders
> who wrote it — and optionally to a dashboard wallet too?"*

**Yes — and this is exactly how it works.**

---

## How the payment flows

```
User / API caller
    │
    │  pays feePerCall (USD-cent denominated, auto-converted via
    │  Chainlink ETH/USD feed to exact wei)
    ▼
financial-ops-rest-server.js
    │  builderFundUsage.record(endpoint)  — in-process counter
    │
    ▼
GET /api/v1/builder-fund/stats   ← read-only snapshot for dashboards / upkeeps
    │
    │  Chainlink Automation upkeep (or trusted ORACLE_ROLE wallet)
    │  reads the stats endpoint and calls:
    │
    ▼
NexusBuilderFund.recordUsage(endpoint_hash, callCount)  ← on-chain
    │
    │  ETH fees arrive via depositFees() or plain receive():
    │
    │  ┌─── placementBps% ──────────────────────────────────────────────┐
    │  │   Auto-forwarded IMMEDIATELY to placementWallet               │
    │  │   (dashboard/treasury wallet — no builder action needed)       │
    │  └───────────────────────────────────────────────────────────────┘
    │
    │  Remainder (100% - placementBps%) accumulates in pool
    │
    ▼
Builder calls claimReward()
    ├──► proportional ETH transferred to builder's wallet
    └──► NGTT token bonus transferred (ngttRewardPerEthWei × ETH claimed)
```

---

## Placement wallet — instant fee routing to the dashboard

Set a `placementWallet` (e.g., the DAO treasury or your dashboard wallet address)
and a `placementBps` (basis points, max 5 000 = 50%).  On **every deposit**,
`placementBps / 10 000` of the ETH is forwarded instantly to that wallet —
no claiming required.

```solidity
// Route 20% of every fee deposit to the dashboard/treasury wallet
builderFund.setPlacementConfig(
    0x33ffc308e693a5b49e0ee0241f41f03ccef495f2, // dashboard wallet
    2000                                          // 20% = 2000 bps
);
```

With `placementBps = 2000`:
- $0.01 fee deposit → $0.002 goes instantly to the treasury wallet
- $0.008 enters the builder pool for proportional claims

Set `placementWallet = address(0)` or `placementBps = 0` to disable.

---

## NGTT token awards for developers

When a builder claims ETH rewards, they **automatically receive NGTT governance
tokens** as an additional bonus, proportional to the ETH claimed.

```solidity
// Award 1 000 NGTT per ETH claimed
builderFund.setNgttRewardConfig(
    0xNGTTTokenAddress,
    1000e18   // 1 000 NGTT per 1 ETH (1e18 wei)
);
```

The contract must hold NGTT tokens (funded by the admin or DAO governance).
If the contract balance is insufficient, the ETH claim still succeeds —
the NGTT bonus is silently skipped until tokens are replenished.

```solidity
// Check how many NGTT tokens the contract holds for awards
uint256 available = builderFund.ngttBalance();
```

---

## Fee denomination

| Denomination | Helper | Example (fee = $0.01) |
|---|---|---|
| ETH (wei) | `getFeeWei()` | ≈ 3 333 wei at ETH = $3 000 |
| Bitcoin (satoshi) | `getFeeSatoshis()` | ≈ 1 666 sat at BTC = $60 000 |

Both use Chainlink AggregatorV3 feeds, with a 1-hour staleness guard.
Price denomination is USD-cents — `feePerCallUsdCents = 1` means **$0.01 per call**.

Setting `feePerCallUsdCents = 0` disables per-call enforcement;
fees are deposited externally (Lightning bridge, GitHub Sponsors, etc.).

---

## Data-driven oracle settlement

The REST server tracks usage **in-process** (zero on-chain gas per call).
A **Chainlink Automation** upkeep (or cron job) polls `/api/v1/builder-fund/stats`,
checks if the accumulated delta is worth a gas fee to record, then submits:

```solidity
builderFund.recordUsage(
    keccak256("/api/v1/member"),
    uint256(deltaCallCount)
);
```

This is the "data-driven" pattern: off-chain event → on-chain settlement,
exactly like Chainlink Keepers / The Graph indexer rewards.

---

## Builder registry

Builders are registered by the DAO admin:

```solidity
// Register FuzzysTodd with 100 shares
builderFund.registerBuilder(
    0x33ffc308e693a5b49e0ee0241f41f03ccef495f2,
    100,
    "FuzzysTodd"
);

// Register a contributor with 50 shares
builderFund.registerBuilder(
    0xContributorWallet,
    50,
    "contributor-github-handle"
);
```

Shares are relative weights. With 100 + 50 = 150 total shares:
- FuzzysTodd receives 100/150 = **66.7%** of all deposited fees.
- Contributor receives 50/150 = **33.3%**.

Shares are updatable by the admin at any time.

---

## REST API

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/builder-fund/stats` | Public | Read-only usage snapshot |
| `POST` | `/api/v1/builder-fund/usage` | `Bearer NEXUS_ORACLE_SECRET` | Oracle records a batch of calls |

### Example: read stats

```bash
curl http://localhost:8788/api/v1/builder-fund/stats
```

```json
{
  "service": "nexus-builder-fund-usage",
  "startedAt": "2026-04-27T19:00:00.000Z",
  "snapshotAt": "2026-04-27T20:00:00.000Z",
  "totalCalls": 1842,
  "byEndpoint": {
    "/api/v1/member": 1204,
    "/api/signals":   412,
    "/api/summary":   226
  },
  "builderFundContract": "0x...",
  "oracleNote": "Submit stats.byEndpoint to NexusBuilderFund.recordUsage() via ORACLE_ROLE."
}
```

### Example: oracle records usage

```bash
curl -X POST http://localhost:8788/api/v1/builder-fund/usage \
  -H "Authorization: Bearer $NEXUS_ORACLE_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"endpoint": "/api/v1/member", "callCount": 1204}'
```

---

## Smart contract

**`contracts/NexusBuilderFund.sol`** — key functions:

| Function | Who calls it | Description |
|---|---|---|
| `registerBuilder(wallet, shares, handle)` | Admin | Add a developer to the fund |
| `updateBuilder(id, shares, active)` | Admin | Change shares or deactivate |
| `depositFees(note)` | Anyone (payable) | Deposit ETH; placement cut auto-forwarded |
| `recordUsage(endpoint, count)` | ORACLE_ROLE | Record off-chain API calls |
| `claimReward()` | Registered builder | Pull proportional ETH + NGTT bonus |
| `setPlacementConfig(wallet, bps)` | Admin | Set placement wallet + basis points |
| `setNgttRewardConfig(token, rate)` | Admin | Set NGTT token address + award rate |
| `getFeeWei()` | View | Current per-call fee in wei (Chainlink) |
| `getFeeSatoshis()` | View | Current per-call fee in satoshis (Chainlink) |
| `pendingReward(builderId)` | View | Claimable ETH for a builder |
| `rewardConfig()` | View | Returns placement + NGTT config in one call |
| `ngttBalance()` | View | NGTT tokens available for awards in contract |
| `builderCount()` | View | Total registered builders |

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `NEXUS_ORACLE_SECRET` | *(empty = no auth)* | Bearer token for POST `/api/v1/builder-fund/usage` |
| `NEXUS_BUILDER_FUND_ADDRESS` | *(empty)* | Deployed contract address (shown in stats) |
| `NEXUS_PLACEMENT_WALLET` | *(empty)* | Dashboard/treasury wallet shown in stats (informational) |
| `NEXUS_PLACEMENT_BPS` | `0` | Basis points shown in stats (mirrors on-chain `placementBps`) |
| `NEXUS_NGTT_TOKEN_ADDRESS` | *(empty)* | NGTT token address shown in stats |
| `NEXUS_NGTT_REWARD_PER_ETH` | *(empty)* | NGTT reward rate shown in stats |

---

## Chainlink Automation upkeep script (example)

```javascript
// upkeep.js — run as a Chainlink Automation compatible job
// or as a simple cron: node upkeep.js
const { ethers } = require("ethers");

const STATS_URL   = process.env.STATS_URL || "http://localhost:8788/api/v1/builder-fund/stats";
const CONTRACT    = process.env.NEXUS_BUILDER_FUND_ADDRESS;
const ORACLE_KEY  = process.env.ORACLE_PRIVATE_KEY;
const RPC_URL     = process.env.RPC_URL;

const ABI = [
    "function recordUsage(bytes32 endpoint, uint256 callCount) external",
];

async function run() {
    const stats = await fetch(STATS_URL).then(r => r.json());
    const provider = new ethers.providers.JsonRpcProvider(RPC_URL);
    const signer   = new ethers.Wallet(ORACLE_KEY, provider);
    const fund     = new ethers.Contract(CONTRACT, ABI, signer);

    for (const [endpoint, count] of Object.entries(stats.byEndpoint)) {
        if (count < 10) continue; // Only worth a tx above 10 calls
        const hash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes(endpoint));
        const tx = await fund.recordUsage(hash, count);
        await tx.wait();
        console.log(`Recorded ${count} calls for ${endpoint}: ${tx.hash}`);
    }
}

run().catch(console.error);
```

---

## Component-Based Expert Registration

Every Nexus code-space component is attributed to an expert domain and registered
as a dedicated builder entry in the fund.  This means the dev-pay system
automatically routes proportional ETH to the maintainer of each code space —
no manual invoicing required.

### The 10 registered expert components

| # | Code Space | Expert Domain | Shares |
|---|-----------|--------------|-------:|
| 1 | `contracts/NexusBuilderFund.sol` | `Solidity-DeFi-Core` | 200 |
| 2 | `contracts/NexusLPStaking.sol` | `Solidity-AMM-Staking` | 150 |
| 3 | `contracts/NexusRWA.sol` | `Solidity-RWA-Compliance` | 150 |
| 4 | `contracts/NexusFractionalize.sol` | `Solidity-NFT-Fractionalization` | 120 |
| 5 | `contracts/NexusOptionsVault.sol` | `Solidity-Options-DeFi` | 180 |
| 6 | `contracts/NexusFractalVault.sol` | `Solidity-Vault-Yield` | 160 |
| 7 | `nexus-signal-bus.js` | `NodeJS-WebSocket-Infra` | 100 |
| 8 | `nexus/e2e_soundness.py` | `Python-QA-Validation` | 80 |
| 9 | `web3-interface.html` | `Frontend-Web3-UX` | 90 |
| 10 | `builder-fund.html` | `Frontend-DApp-UX` | 70 |

See [`docs/EXPERT_REGISTRY.md`](EXPERT_REGISTRY.md) for full rationale, wallet
env vars, and the registration script usage guide.

### Registering component experts

Use the `scripts/register-expert-builders.js` script after deployment:

```bash
# Dry run — preview all 10 registrations without broadcasting
DRY_RUN=true node scripts/register-expert-builders.js

# Live run — registers all 10 expert roles on-chain
NEXUS_BUILDER_FUND_ADDRESS=0x... \
ADMIN_PRIVATE_KEY=<key> \
RPC_URL=https://mainnet.infura.io/v3/<id> \
node scripts/register-expert-builders.js
```

### Updated `registerBuilder` signature

The contract now supports an optional `component` parameter for expert-domain
attribution (backward-compatible overload — existing calls with 3 params still work):

```solidity
// 4-param overload — with expert-domain attribution
builderFund.registerBuilder(
    0xExpertWallet,
    200,
    "nexus-solidity-defi-expert",
    "Solidity-DeFi-Core"         // ← component field
);

// 3-param legacy overload — component defaults to ""
builderFund.registerBuilder(
    0xContributorWallet,
    50,
    "contributor-github-handle"
);
```

### Querying component attribution on-chain

```solidity
// Which builder IDs are attributed to the Solidity-DeFi-Core component?
uint256[] memory ids = builderFund.buildersByComponent("Solidity-DeFi-Core");

// Get full builder record including component field
NexusBuilderFund.Builder memory b = builderFund.getBuilder(ids[0]);
// b.component == "Solidity-DeFi-Core"
// b.handle    == "nexus-solidity-defi-expert"
// b.shares    == 200
```

### Component usage in the REST API

The `/api/v1/builder-fund/stats` endpoint now includes the `expertRegistry`
field — a JSON array of all 10 registered components with their handles, share
weights, and code-space paths:

```json
{
  "service": "nexus-builder-fund-usage",
  "expertRegistry": [
    { "handle": "nexus-solidity-defi-expert", "component": "Solidity-DeFi-Core", "shares": 200, "codeSpace": "contracts/NexusBuilderFund.sol" },
    ...
  ]
}
```

---

## Academic alignment

- **Protocol Guild** (Ethereum core dev funding) — exact same share-weight pool pattern
- **MIT 15.S12 (Blockchain & Money)** — data-driven settlement without intermediaries
- **Wharton** — proportional revenue share as an incentive alignment mechanism
- **Chainlink Functions / Automation** — the "data-driven" oracle bridge between off-chain usage and on-chain payment

---

*Part of the Nexus Protocol DAO strategic plan — Phase 2 signal bus / builder compensation.*
*Owner: @FuzzysTodd — governed by GOVERNANCE.md.*
