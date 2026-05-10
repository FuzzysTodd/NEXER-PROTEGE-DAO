# Nexus Protocol DAO — Governance Implementation Guide

> **Status:** Phase 1 complete — contract foundation deployed and tested.  
> **Authority:** All deployments, parameter changes, and treasury actions require explicit approval by @FuzzysTodd per `GOVERNANCE.md`.

---

## Overview

This document describes the full on-chain governance architecture for the Nexus Protocol DAO. It covers contract design, deployment parameters, role assignment, upgrade paths, and operational runbooks.

---

## Architecture

```
 ┌─────────────────────────────────────────────────────────────┐
 │                  Nexus Protocol DAO Stack                    │
 │                                                             │
 │  ┌─────────────────────┐   vote weight   ┌───────────────┐ │
 │  │  NGTTGovernanceToken │──────────────►│  NexusDAO-    │ │
 │  │  (ERC20Votes +       │                │  Governor     │ │
 │  │   ERC20Permit)       │◄──────────────│  (propose /   │ │
 │  └─────────────────────┘  delegation    │   vote /      │ │
 │                                         │   queue /     │ │
 │  ┌─────────────────────┐◄──queue/exec──│   execute)    │ │
 │  │  NexusDAOTimelock    │               └───────────────┘ │
 │  │  (2-day delay)       │                                  │
 │  └──────────┬──────────┘                                  │
 │             │ EXECUTOR_ROLE                               │
 │  ┌──────────▼──────────┐                                  │
 │  │  NexusDAOTreasury    │                                  │
 │  │  (ETH + ERC-20)      │                                  │
 │  └─────────────────────┘                                  │
 └─────────────────────────────────────────────────────────────┘
```

---

## Contracts

### `contracts/NGTTGovernanceToken.sol`

| Property | Value |
|---|---|
| Name | Nexus Game Theory Token |
| Symbol | NGTT |
| Total supply | 1 000 000 000 NGTT (1 billion, 18 decimals) |
| Standard | ERC-20 + ERC20Votes + ERC20Permit |
| Voting | Snapshot-based; holders must call `delegate(address)` once |
| Owner | Transferred to `NexusDAOTimelock` post-deployment |

**Key additions vs original `NexusGameTheoryToken.sol`:**

- `delegate(address)` / `delegateBySig(…)` — activate voting weight.
- `getVotes(address)` — current voting power.
- `getPastVotes(address, blockNumber)` — historical snapshot (used by Governor).
- `getPastTotalSupply(blockNumber)` — historical total supply (used for quorum).
- All existing MCP group, game-reward, and profit-pool functions are preserved.

---

### `contracts/NexusDAOTimelock.sol`

| Property | Value |
|---|---|
| Minimum delay | **2 days** (172 800 seconds) |
| PROPOSER_ROLE | `NexusDAOGovernor` |
| EXECUTOR_ROLE | `address(0)` (anyone may execute when delay has elapsed) |
| CANCELLER_ROLE | Owner + Super Delegates (emergency veto) |
| TIMELOCK_ADMIN_ROLE | Renounced post-setup (self-administered) |

The Timelock is the **sole** mechanism through which governance decisions are executed. Passing a proposal in the Governor does not immediately execute it; it queues an operation here that may run only after the delay.

---

### `contracts/NexusDAOGovernor.sol`

| Parameter | Value | Adjustable |
|---|---|---|
| Voting delay | **7 200 blocks** (~1 day at 12 s/block) | Via governance |
| Voting period | **50 400 blocks** (~7 days at 12 s/block) | Via governance |
| Proposal threshold | **10 000 NGTT** | Via governance |
| Quorum | **4%** of total supply at snapshot block | Via governance |
| Timelock | `NexusDAOTimelock` | Fixed at deploy |
| Vote token | `NGTTGovernanceToken` | Fixed at deploy |

**Proposal lifecycle:**

```
propose()          → ProposalState.Pending
[voting delay]     → ProposalState.Active
castVote()         → (votes recorded)
[voting period]    → ProposalState.Succeeded / Defeated
queue()            → ProposalState.Queued  (timelock starts)
[timelock delay]   → ProposalState.Queued  (waiting)
execute()          → ProposalState.Executed
```

Any queued proposal can be cancelled by an address holding `CANCELLER_ROLE` on the Timelock before execution.

---

### `contracts/NexusDAOTreasury.sol`

| Role | Holder | Capability |
|---|---|---|
| `EXECUTOR_ROLE` | `NexusDAOTimelock` | Transfer ETH and ERC-20 tokens |
| `GUARDIAN_ROLE` | Owner + Super Delegates | Pause / unpause transfers |
| `DEFAULT_ADMIN_ROLE` | Owner wallet | Grant / revoke roles |

The Treasury emits a descriptive event for every state change (`ETHDeposited`, `ETHTransferred`, `ERC20Deposited`, `ERC20Transferred`, `TreasuryPaused`, `TreasuryUnpaused`).

---

## Deployment Procedure

### Prerequisites

```bash
npm install --save-dev hardhat @openzeppelin/contracts dotenv
```

### Environment

Create `.env` in the repository root (never commit this file):

```
OWNER_ADDRESS=0x33ffc308e693a5b49e0ee0241f41f03ccef495f2
# Add RPC_URL and DEPLOYER_PRIVATE_KEY for Hardhat (use hardware wallet on mainnet)
```

### Testnet deployment

```bash
npx hardhat run scripts/deploy_dao.js --network sepolia
```

### Mainnet deployment

```bash
# 1. Dry-run on a local fork first
npx hardhat run scripts/deploy_dao.js --network hardhat

# 2. Deploy on mainnet with hardware wallet signer
npx hardhat run scripts/deploy_dao.js --network mainnet
```

### Post-deployment checklist

- [ ] Verify all four contracts on Etherscan.
- [ ] Save the deployed addresses in `docs/DEPLOYED_ADDRESSES.md`.
- [ ] Confirm roles: Governor has `PROPOSER_ROLE` on Timelock; Timelock has `EXECUTOR_ROLE` on Treasury.
- [ ] Confirm `TIMELOCK_ADMIN_ROLE` has been revoked from the deployer.
- [ ] Confirm NGTT token ownership transferred to Timelock.
- [ ] Announce to NGTT holders: each holder must call `delegate(address)` to activate their votes.
- [ ] Update `governance.html` with live contract addresses (Phase 2).

---

## Voter / Delegate Guide

### Activating your votes

NGTT holders have no voting power until they explicitly delegate:

```javascript
// Self-delegate (keep your own voting power)
await ngtt.delegate(myWalletAddress);

// Delegate to a trusted Super Delegate
await ngtt.delegate(superDelegateAddress);
```

This only needs to be done once. Your vote weight will update automatically with every token transfer thereafter.

### Submitting a proposal

To submit a proposal you need at least **10 000 NGTT** delegated to your address at the snapshot block.

```javascript
const targets   = [treasuryAddress];
const values    = [0];
const calldatas = [treasury.interface.encodeFunctionData(
  "transferETH", [recipient, ethers.utils.parseEther("1.0"), "Q2 grant"])];
const description = "NXP-013: Transfer 1 ETH to grant recipient";

await governor.propose(targets, values, calldatas, description);
```

### Casting a vote

```javascript
// 0 = Against, 1 = For, 2 = Abstain
await governor.castVote(proposalId, 1);

// With reason (emitted in event)
await governor.castVoteWithReason(proposalId, 1, "Supports the Q2 roadmap");
```

### Queuing and executing

After the voting period ends with a majority:

```javascript
// Anyone can queue
await governor.queue(targets, values, calldatas, descriptionHash);

// After 2-day timelock delay, anyone can execute
await governor.execute(targets, values, calldatas, descriptionHash);
```

---

## Security Model

### Reentrancy

All fund-handling functions in `NexusDAOTreasury` and `NGTTGovernanceToken` use `ReentrancyGuard` / `nonReentrant`.

### Access control

| Action | Who |
|---|---|
| Propose | Any holder with ≥ 10 000 NGTT delegated |
| Vote | Any NGTT holder who has called `delegate()` |
| Queue | Anyone (after vote succeeds) |
| Execute | Anyone (after timelock delay) |
| Cancel (queued) | `CANCELLER_ROLE` — Owner + Super Delegates |
| Treasury ETH / ERC-20 transfer | `EXECUTOR_ROLE` on Treasury = Timelock only |
| Treasury pause | `GUARDIAN_ROLE` — Owner + Super Delegates |
| NGTT minting / profit ops | Timelock only (post-ownership-transfer) |

### Timelock safety

The mandatory 2-day delay between a passed vote and execution gives token holders time to exit or challenge dangerous proposals before they take effect.

### Parameter changes

Voting delay, voting period, proposal threshold, and quorum are all adjustable via governance (no special role needed). This means any malicious change to these parameters must itself go through a full vote + timelock cycle.

---

## Emergency Incident Response

### Step 1 — Pause the treasury

If a malicious proposal has been queued, an address holding `GUARDIAN_ROLE` on the Treasury can pause outflows:

```javascript
await treasury.pause();
```

### Step 2 — Cancel the queued operation

An address holding `CANCELLER_ROLE` on the Timelock can cancel:

```javascript
await timelock.cancel(operationId);
```

### Step 3 — Unpause and resume normal operations

After the threat is resolved:

```javascript
await treasury.unpause();
```

### Step 4 — File a post-mortem

Document the incident in `docs/` and submit a governance proposal to patch the root cause.

---

## Phase Roadmap

| Phase | Status | Deliverable |
|---|---|---|
| Phase 1 | ✅ Complete | Smart contract foundation, tests, deploy script, this doc |
| Phase 2 | Planned | Wire `governance.html` to live contracts (real proposal/vote flows) |
| Phase 3 | Planned | Chainlink oracle integration for BTC-backing ratio enforcement |
| Phase 4 | Planned | Cross-chain bridge relay (Base / L2 governance mirroring) |
| Phase 5 | Planned | Independent security audit and mainnet launch |

---

## References

- `GOVERNANCE.md` — Authority structure and DAO operating mandate
- `contracts/NGTTGovernanceToken.sol` — Votes-enabled NGTT token
- `contracts/NexusDAOTimelock.sol` — Timelock controller
- `contracts/NexusDAOGovernor.sol` — Governor contract
- `contracts/NexusDAOTreasury.sol` — Treasury module
- `scripts/deploy_dao.js` — Deployment script
- `docs/NEXUS_ENCRYPTION_STANDARD.md` — NES signing standard
- [OpenZeppelin Governor Docs](https://docs.openzeppelin.com/contracts/4.x/governance)
