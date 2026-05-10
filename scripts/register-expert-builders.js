// SPDX-License-Identifier: MIT
// scripts/register-expert-builders.js
//
// Expert-Domain Attribution & Dev-Pay Registration for the 10 Nexus Code Spaces.
//
// Registers each of the 10 major Nexus Protocol code-space components as a
// builder entry in NexusBuilderFund.sol via `registerBuilder(wallet, shares,
// handle, component)`.
//
// ─── USAGE ───────────────────────────────────────────────────────────────────
//   Required env vars:
//     NEXUS_BUILDER_FUND_ADDRESS  — deployed contract address
//     ADMIN_PRIVATE_KEY           — DEFAULT_ADMIN_ROLE private key (no 0x prefix needed)
//     RPC_URL                     — JSON-RPC endpoint (Infura, Alchemy, local node, …)
//
//   Optional env vars:
//     DRY_RUN=true                — log registrations without broadcasting any tx
//     SKIP_EXISTING=true          — skip wallets already registered (default: true)
//
// ─── DRY RUN ─────────────────────────────────────────────────────────────────
//   DRY_RUN=true node scripts/register-expert-builders.js
//
// ─── LIVE RUN ────────────────────────────────────────────────────────────────
//   NEXUS_BUILDER_FUND_ADDRESS=0x... \
//   ADMIN_PRIVATE_KEY=<key> \
//   RPC_URL=https://mainnet.infura.io/v3/<id> \
//   node scripts/register-expert-builders.js
//
// ─── SECURITY NOTE ───────────────────────────────────────────────────────────
//   Never commit ADMIN_PRIVATE_KEY to source control.  Use .env files that are
//   listed in .gitignore, or inject the variable from a secrets manager at
//   runtime (GitHub Actions secrets, Doppler, etc.).
// ─────────────────────────────────────────────────────────────────────────────

"use strict";

// ─── Configuration ────────────────────────────────────────────────────────────

const CONTRACT_ADDRESS = (process.env.NEXUS_BUILDER_FUND_ADDRESS || "").trim();
const ADMIN_PRIVATE_KEY = (process.env.ADMIN_PRIVATE_KEY || "").trim();
const RPC_URL = (process.env.RPC_URL || "").trim();
const DRY_RUN = (process.env.DRY_RUN || "").toLowerCase() === "true";
const SKIP_EXISTING = (process.env.SKIP_EXISTING || "true").toLowerCase() !== "false";

// ─── Minimal ABI (only the functions this script calls) ──────────────────────

const BUILDER_FUND_ABI = [
  // 4-param overload (with component attribution)
  "function registerBuilder(address wallet, uint256 shares, string calldata handle, string calldata component) external returns (uint256)",
  // View: check if wallet already registered (builderIndex returns builderId+1, 0 = not registered)
  "function builderIndex(address wallet) external view returns (uint256)",
  // Event for confirmation parsing
  "event BuilderRegistered(uint256 indexed builderId, address indexed wallet, string handle, uint256 shares, string component)",
];

// ─── Expert Registry — 10 Nexus Code-Space Components ────────────────────────
//
// Each entry registers ONE expert role for the given component.
// The wallet field uses address(1) as a sentinel placeholder in dry-run mode.
// In a live deployment, replace each wallet with the actual expert's address
// or leave as-is to use a shared admin wallet that can distribute later.
//
// Rationale for share weights (relative to FuzzysTodd's 100-share baseline):
//   200 — NexusBuilderFund.sol core: highest complexity, treasury security risk
//   180 — NexusOptionsVault.sol: complex DeFi math, liquidation risk
//   160 — NexusFractalVault.sol: multi-strategy yield, upgrade surface
//   150 — NexusLPStaking.sol: AMM staking, reward accounting risk
//   150 — NexusRWA.sol: compliance surface, off-chain oracle dependency
//   120 — NexusFractionalize.sol: NFT custody, ERC-20/ERC-721 interaction
//   100 — nexus-signal-bus.js: WebSocket infra, real-time reliability
//    90 — web3-interface.html: frontend Web3 UX, wallet injection surface
//    80 — nexus/e2e_soundness.py: Python QA pipeline, CI reliability
//    70 — builder-fund.html: DApp UX, read-only display surface
// ─────────────────────────────────────────────────────────────────────────────

const EXPERT_COMPONENTS = [
  {
    handle: "nexus-solidity-defi-expert",
    component: "Solidity-DeFi-Core",
    shares: 200,
    codeSpace: "contracts/NexusBuilderFund.sol",
    rationale: "Core treasury contract. Highest complexity and direct fund-security risk.",
    // Replace with actual expert wallet; placeholder keeps script safe in dry-run.
    wallet: process.env.EXPERT_WALLET_SOLIDITY_DEFI || "0x0000000000000000000000000000000000000001",
  },
  {
    handle: "nexus-lp-staking-expert",
    component: "Solidity-AMM-Staking",
    shares: 150,
    codeSpace: "contracts/NexusLPStaking.sol",
    rationale: "AMM LP staking rewards, rounding, and flash-loan vector surface.",
    wallet: process.env.EXPERT_WALLET_LP_STAKING || "0x0000000000000000000000000000000000000002",
  },
  {
    handle: "nexus-rwa-compliance-expert",
    component: "Solidity-RWA-Compliance",
    shares: 150,
    codeSpace: "contracts/NexusRWA.sol",
    rationale: "Real-World Asset compliance surface; off-chain oracle dependency.",
    wallet: process.env.EXPERT_WALLET_RWA || "0x0000000000000000000000000000000000000003",
  },
  {
    handle: "nexus-nft-fractionalize-expert",
    component: "Solidity-NFT-Fractionalization",
    shares: 120,
    codeSpace: "contracts/NexusFractionalize.sol",
    rationale: "NFT custody + ERC-20/ERC-721 interaction surface; vault lock risk.",
    wallet: process.env.EXPERT_WALLET_FRACTIONALIZE || "0x0000000000000000000000000000000000000004",
  },
  {
    handle: "nexus-options-defi-expert",
    component: "Solidity-Options-DeFi",
    shares: 180,
    codeSpace: "contracts/NexusOptionsVault.sol",
    rationale: "Options vault; complex DeFi pricing math and liquidation risk.",
    wallet: process.env.EXPERT_WALLET_OPTIONS || "0x0000000000000000000000000000000000000005",
  },
  {
    handle: "nexus-vault-yield-expert",
    component: "Solidity-Vault-Yield",
    shares: 160,
    codeSpace: "contracts/NexusFractalVault.sol",
    rationale: "Multi-strategy yield vault; upgrade surface and strategy migration risk.",
    wallet: process.env.EXPERT_WALLET_FRACTAL_VAULT || "0x0000000000000000000000000000000000000006",
  },
  {
    handle: "nexus-nodejs-infra-expert",
    component: "NodeJS-WebSocket-Infra",
    shares: 100,
    codeSpace: "nexus-signal-bus.js",
    rationale: "Real-time WebSocket signal bus; uptime and relay reliability.",
    wallet: process.env.EXPERT_WALLET_NODE_INFRA || "0x0000000000000000000000000000000000000007",
  },
  {
    handle: "nexus-python-qa-expert",
    component: "Python-QA-Validation",
    shares: 80,
    codeSpace: "nexus/e2e_soundness.py",
    rationale: "End-to-end soundness validation; CI/CD reliability and test coverage.",
    wallet: process.env.EXPERT_WALLET_PYTHON_QA || "0x0000000000000000000000000000000000000008",
  },
  {
    handle: "nexus-frontend-web3-expert",
    component: "Frontend-Web3-UX",
    shares: 90,
    codeSpace: "web3-interface.html",
    rationale: "Browser-facing wallet injection and transaction UX surface.",
    wallet: process.env.EXPERT_WALLET_FRONTEND_WEB3 || "0x0000000000000000000000000000000000000009",
  },
  {
    handle: "nexus-frontend-dapp-expert",
    component: "Frontend-DApp-UX",
    shares: 70,
    codeSpace: "builder-fund.html",
    rationale: "Builder fund DApp UX; read-only dashboard and claim interface.",
    wallet: process.env.EXPERT_WALLET_FRONTEND_DAPP || "0x000000000000000000000000000000000000000a",
  },
];

// ─── Helpers ─────────────────────────────────────────────────────────────────

function log(msg) {
  process.stdout.write(`[register-expert-builders] ${msg}\n`);
}

function logWarn(msg) {
  process.stderr.write(`[register-expert-builders] WARN: ${msg}\n`);
}

function logError(msg) {
  process.stderr.write(`[register-expert-builders] ERROR: ${msg}\n`);
}

function padRight(str, width) {
  return String(str).padEnd(width, " ");
}

function printSummaryTable() {
  log("─────────────────────────────────────────────────────────────────────────");
  log("  Expert Component Registration Plan");
  log("─────────────────────────────────────────────────────────────────────────");
  log(`  ${"#".padEnd(3)} ${"Handle".padEnd(38)} ${"Component".padEnd(34)} ${"Shares"}`);
  log(`  ${"─".repeat(3)} ${"─".repeat(38)} ${"─".repeat(34)} ${"─".repeat(6)}`);
  EXPERT_COMPONENTS.forEach((entry, i) => {
    log(`  ${String(i + 1).padEnd(3)} ${padRight(entry.handle, 38)} ${padRight(entry.component, 34)} ${entry.shares}`);
  });
  const totalShares = EXPERT_COMPONENTS.reduce((acc, e) => acc + e.shares, 0);
  log(`  ${"─".repeat(3)} ${"─".repeat(38)} ${"─".repeat(34)} ${"─".repeat(6)}`);
  log(`  ${"".padEnd(3)} ${"TOTAL".padEnd(38)} ${"".padEnd(34)} ${totalShares}`);
  log("─────────────────────────────────────────────────────────────────────────");
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  log(`Mode: ${DRY_RUN ? "DRY RUN (no transactions will be broadcast)" : "LIVE"}`);
  printSummaryTable();

  if (!DRY_RUN) {
    // ethers is only required in live mode — keeps dry-run dependency-free
    // eslint-disable-next-line global-require
    const { ethers } = require("ethers");

    // Validate required env vars for live run
    if (!CONTRACT_ADDRESS) {
      logError("NEXUS_BUILDER_FUND_ADDRESS env var is required for live run.");
      process.exit(1);
    }
    if (!ethers.isAddress(CONTRACT_ADDRESS)) {
      logError(`NEXUS_BUILDER_FUND_ADDRESS "${CONTRACT_ADDRESS}" is not a valid Ethereum address.`);
      process.exit(1);
    }
    if (!ADMIN_PRIVATE_KEY) {
      logError("ADMIN_PRIVATE_KEY env var is required for live run.");
      process.exit(1);
    }
    if (!RPC_URL) {
      logError("RPC_URL env var is required for live run.");
      process.exit(1);
    }
  }

  let contract = null;
  let signer = null;
  let ethers = null;

  if (!DRY_RUN) {
    // eslint-disable-next-line global-require
    ethers = require("ethers").ethers;
    const provider = new ethers.JsonRpcProvider(RPC_URL);
    signer = new ethers.Wallet(ADMIN_PRIVATE_KEY, provider);
    contract = new ethers.Contract(CONTRACT_ADDRESS, BUILDER_FUND_ABI, signer);
    log(`Connected to ${CONTRACT_ADDRESS} via ${RPC_URL}`);
    log(`Admin signer: ${signer.address}`);
  }

  const results = [];

  for (let i = 0; i < EXPERT_COMPONENTS.length; i++) {
    const entry = EXPERT_COMPONENTS[i];
    const tag = `[${i + 1}/${EXPERT_COMPONENTS.length}] ${entry.handle}`;

    if (DRY_RUN) {
      log(`${tag} — DRY RUN: would call registerBuilder(`);
      log(`    wallet    = ${entry.wallet}`);
      log(`    shares    = ${entry.shares}`);
      log(`    handle    = "${entry.handle}"`);
      log(`    component = "${entry.component}"`);
      log(`  ) — code space: ${entry.codeSpace}`);
      results.push({ ...entry, status: "dry-run", txHash: null });
      continue;
    }

    // Check if already registered (SKIP_EXISTING guard)
    if (SKIP_EXISTING) {
      const existingIndex = await contract.builderIndex(entry.wallet);
      if (existingIndex > 0n) {
        log(`${tag} — SKIP: wallet ${entry.wallet} already registered (builderId ${Number(existingIndex) - 1})`);
        results.push({ ...entry, status: "skipped", txHash: null });
        continue;
      }
    }

    // Validate wallet is a real address (skip zero-address placeholders in live mode)
    // ethers is guaranteed to be loaded at this point (only reached when !DRY_RUN)
    if (!ethers.isAddress(entry.wallet) || /^0x0+[0-9a-fA-F]?$/.test(entry.wallet)) {
      logWarn(`${tag} — wallet "${entry.wallet}" looks like a placeholder. Set EXPERT_WALLET_* env vars for live registration. Skipping.`);
      results.push({ ...entry, status: "skipped-placeholder", txHash: null });
      continue;
    }

    try {
      log(`${tag} — sending registerBuilder tx...`);
      const tx = await contract.registerBuilder(
        entry.wallet,
        entry.shares,
        entry.handle,
        entry.component
      );
      log(`${tag} — tx broadcast: ${tx.hash}`);
      const receipt = await tx.wait();
      log(`${tag} — confirmed in block ${receipt.blockNumber} (gas: ${receipt.gasUsed.toString()})`);
      results.push({ ...entry, status: "registered", txHash: tx.hash });
    } catch (err) {
      logError(`${tag} — registration failed: ${err.message}`);
      results.push({ ...entry, status: "error", txHash: null, error: err.message });
    }
  }

  // ─── Results summary ──────────────────────────────────────────────────────
  log("─────────────────────────────────────────────────────────────────────────");
  log("  Registration Results");
  log("─────────────────────────────────────────────────────────────────────────");
  for (const r of results) {
    const statusLabel = r.status.padEnd(20);
    const txInfo = r.txHash ? ` tx=${r.txHash}` : "";
    const errInfo = r.error ? ` err=${r.error}` : "";
    log(`  ${statusLabel} ${r.handle}${txInfo}${errInfo}`);
  }
  log("─────────────────────────────────────────────────────────────────────────");

  const registered = results.filter((r) => r.status === "registered").length;
  const skipped = results.filter((r) => r.status.startsWith("skipped")).length;
  const errors = results.filter((r) => r.status === "error").length;
  const dryRun = results.filter((r) => r.status === "dry-run").length;

  if (DRY_RUN) {
    log(`Dry-run complete. ${dryRun} entries would be registered.`);
  } else {
    log(`Done. registered=${registered}  skipped=${skipped}  errors=${errors}`);
  }

  if (errors > 0) {
    process.exit(1);
  }
}

main().catch((err) => {
  logError(err.stack || err.message);
  process.exit(1);
});
