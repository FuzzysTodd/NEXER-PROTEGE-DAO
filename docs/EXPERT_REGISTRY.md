# Nexus Expert Registry — Component Attribution & Dev-Pay

## Overview

The **Expert Registry** maps each of the 10 major Nexus Protocol code-space
components to an expert domain and a dev-pay weight in the
[NexusBuilderFund](../contracts/NexusBuilderFund.sol).

Every expert role is a registered builder entry.  When ETH fee revenue flows
into the fund, each expert's proportional share of the pool is determined by
their `shares` weight relative to the sum of all active builder shares.

---

## Component → Expert Domain Mapping

| # | Code Space | Expert Domain (`component`) | Shares | Rationale |
|---|-----------|---------------------------|-------:|-----------|
| 1 | `contracts/NexusBuilderFund.sol` | `Solidity-DeFi-Core` | **200** | Core treasury contract. Highest complexity, direct fund-security surface. |
| 2 | `contracts/NexusLPStaking.sol` | `Solidity-AMM-Staking` | **150** | AMM LP staking rewards, rounding edge-cases, flash-loan attack surface. |
| 3 | `contracts/NexusRWA.sol` | `Solidity-RWA-Compliance` | **150** | Real-World Asset compliance; off-chain oracle dependency and legal surface. |
| 4 | `contracts/NexusFractionalize.sol` | `Solidity-NFT-Fractionalization` | **120** | NFT custody + ERC-20/ERC-721 interaction surface; vault-lock risk. |
| 5 | `contracts/NexusOptionsVault.sol` | `Solidity-Options-DeFi` | **180** | Options vault; complex DeFi pricing math and liquidation exposure. |
| 6 | `contracts/NexusFractalVault.sol` | `Solidity-Vault-Yield` | **160** | Multi-strategy yield vault; upgrade path and strategy migration risk. |
| 7 | `nexus-signal-bus.js` | `NodeJS-WebSocket-Infra` | **100** | Real-time WebSocket signal bus; relay uptime and oracle reliability. |
| 8 | `nexus/e2e_soundness.py` | `Python-QA-Validation` | **80** | End-to-end soundness test suite; CI/CD reliability, regression coverage. |
| 9 | `web3-interface.html` | `Frontend-Web3-UX` | **90** | Browser-facing wallet injection and transaction UX surface. |
| 10 | `builder-fund.html` | `Frontend-DApp-UX` | **70** | Builder fund DApp UX; read-only dashboard and claim interface. |

> **Share weight rationale** — weights are proportional to complexity, security
> risk, and maintenance burden.  Solidity contracts touching treasury funds
> carry the highest weights; read-only frontend surfaces the lowest.

### Total expert shares: 1 300

With the primary owner (@FuzzysTodd, `0x33ffc308e693a5b49e0ee0241f41f03ccef495f2`)
holding **100 shares** as the baseline, the grand total across all builders is
**1 400 shares** (100 + 1 300).  FuzzysTodd's cut is `100 / 1400 ≈ 7.1%` of
all fee revenue; each expert receives their proportional slice of the remaining
92.9%.

---

## Builder Handles

| Handle | Component |
|--------|-----------|
| `FuzzysTodd` | Primary owner / cross-cutting |
| `nexus-solidity-defi-expert` | `Solidity-DeFi-Core` |
| `nexus-lp-staking-expert` | `Solidity-AMM-Staking` |
| `nexus-rwa-compliance-expert` | `Solidity-RWA-Compliance` |
| `nexus-nft-fractionalize-expert` | `Solidity-NFT-Fractionalization` |
| `nexus-options-defi-expert` | `Solidity-Options-DeFi` |
| `nexus-vault-yield-expert` | `Solidity-Vault-Yield` |
| `nexus-nodejs-infra-expert` | `NodeJS-WebSocket-Infra` |
| `nexus-python-qa-expert` | `Python-QA-Validation` |
| `nexus-frontend-web3-expert` | `Frontend-Web3-UX` |
| `nexus-frontend-dapp-expert` | `Frontend-DApp-UX` |

---

## How to Run the Registration Script

### Prerequisites

1. A deployed `NexusBuilderFund` contract address.
2. The `DEFAULT_ADMIN_ROLE` private key.
3. An RPC endpoint (Infura, Alchemy, or local node).
4. Node.js ≥ 18 with `ethers` v6 installed.

```bash
npm install ethers
```

### Dry run (no transactions)

```bash
DRY_RUN=true node scripts/register-expert-builders.js
```

Prints the full registration plan — component, handle, shares — without
broadcasting any transactions.

### Live run

```bash
NEXUS_BUILDER_FUND_ADDRESS=0xYourContractAddress \
ADMIN_PRIVATE_KEY=your_private_key_here \
RPC_URL=https://mainnet.infura.io/v3/YOUR_PROJECT_ID \
node scripts/register-expert-builders.js
```

By default the script skips wallets that are already registered
(`SKIP_EXISTING=true`).  Set `SKIP_EXISTING=false` to attempt re-registration
(the contract will revert with "already registered" — no funds are lost).

### Setting expert wallets

Each expert's payment destination is read from an environment variable.
Override the defaults (zero-address sentinels) before going live:

| Env var | Component |
|---------|-----------|
| `EXPERT_WALLET_SOLIDITY_DEFI` | `Solidity-DeFi-Core` |
| `EXPERT_WALLET_LP_STAKING` | `Solidity-AMM-Staking` |
| `EXPERT_WALLET_RWA` | `Solidity-RWA-Compliance` |
| `EXPERT_WALLET_FRACTIONALIZE` | `Solidity-NFT-Fractionalization` |
| `EXPERT_WALLET_OPTIONS` | `Solidity-Options-DeFi` |
| `EXPERT_WALLET_FRACTAL_VAULT` | `Solidity-Vault-Yield` |
| `EXPERT_WALLET_NODE_INFRA` | `NodeJS-WebSocket-Infra` |
| `EXPERT_WALLET_PYTHON_QA` | `Python-QA-Validation` |
| `EXPERT_WALLET_FRONTEND_WEB3` | `Frontend-Web3-UX` |
| `EXPERT_WALLET_FRONTEND_DAPP` | `Frontend-DApp-UX` |

> **Security:** Never embed private keys or wallet addresses in source files.
> Use `.env` files (gitignored) or a secrets manager.

---

## How Component Attribution Feeds Into Dev Pay

```
Code-space component usage
    │
    │  Every API call that touches a component is tracked in-process
    │  by financial-ops-rest-server.js (builderFundUsage.record()).
    │
    ▼
GET /api/v1/builder-fund/stats
    │  Returns byEndpoint call counts AND expertRegistry (component list).
    │
    │  A Chainlink Automation upkeep or cron job polls this endpoint and
    │  submits:
    │
    ▼
NexusBuilderFund.recordUsage(endpoint_hash, callCount)  ← on-chain oracle
    │
    │  ETH fee deposits arrive via depositFees() or plain receive().
    │  The contract auto-forwards placementBps to the treasury wallet.
    │  The remainder accumulates in the builder pool.
    │
    ▼
Expert builder calls claimReward()
    ├──► proportional ETH transferred (shares / totalShares × pool)
    └──► NGTT governance token bonus (ngttRewardPerEthWei × ETH)
```

### On-chain component query

After registration, you can query which builder IDs belong to a component:

```solidity
uint256[] memory ids = builderFund.buildersByComponent("Solidity-DeFi-Core");
// ids = [1]  (builderId of nexus-solidity-defi-expert)
```

Or retrieve the full builder record (including component field):

```solidity
NexusBuilderFund.Builder memory b = builderFund.getBuilder(1);
// b.component == "Solidity-DeFi-Core"
// b.handle    == "nexus-solidity-defi-expert"
// b.shares    == 200
```

---

## Smart Contract Reference

### Updated `Builder` struct

```solidity
struct Builder {
    address wallet;       // Payment destination
    uint256 shares;       // Relative weight in the pool
    string  handle;       // GitHub handle or display name
    string  component;    // Expert domain (e.g., "Solidity-DeFi-Core")
    uint256 totalClaimed; // Cumulative ETH (wei) ever claimed
    bool    active;       // False = removed but history kept
}
```

### Updated `BuilderRegistered` event

```solidity
event BuilderRegistered(
    uint256 indexed builderId,
    address indexed wallet,
    string  handle,
    uint256 shares,
    string  component   // ← NEW: expert domain attribution
);
```

### New registration overload

```solidity
// 4-param overload — with explicit component attribution
function registerBuilder(
    address wallet,
    uint256 shares,
    string calldata handle,
    string calldata component
) external onlyRole(DEFAULT_ADMIN_ROLE) returns (uint256 builderId);

// Legacy 3-param overload — component defaults to ""
function registerBuilder(
    address wallet,
    uint256 shares,
    string calldata handle
) external onlyRole(DEFAULT_ADMIN_ROLE) returns (uint256 builderId);
```

### New view function

```solidity
// Returns all builderIds attributed to a given component
function buildersByComponent(string calldata component)
    external view returns (uint256[] memory ids);
```

---

## Academic Alignment

- **Protocol Guild** — Ethereum core-dev funding; exact same share-weight pool pattern
- **Gitcoin Grants** — contributor-level attribution for open-source code spaces
- **MIT 15.S12** — data-driven settlement: off-chain usage → on-chain payment
- **Chainlink Automation** — oracle bridge between component API calls and ETH distribution

---

*Part of the Nexus Protocol DAO strategic plan — Phase 2 builder compensation.*  
*Owner: @FuzzysTodd — governed by GOVERNANCE.md.*
