/**
 * deploy_dao.js — Nexus Protocol DAO Deployment Script
 *
 * Deploys the four core Nexus DAO contracts in the correct dependency order
 * and wires up all role assignments so the system is fully self-governed.
 *
 * Usage (Hardhat):
 *   npx hardhat run scripts/deploy_dao.js --network <network>
 *
 * Required environment variables (set via .env or CI secrets):
 *   OWNER_ADDRESS   — The @FuzzysTodd owner wallet address.
 *
 * Deployment order:
 *   1. NGTTGovernanceToken  — votes-enabled NGTT token
 *   2. NexusDAOTimelock     — timelocked executor (2-day delay)
 *   3. NexusDAOGovernor     — on-chain proposal & voting engine
 *   4. NexusDAOTreasury     — DAO-controlled fund vault
 *   5. Role assignment ceremony
 *
 * Role assignment ceremony (step 5):
 *   a. Grant Timelock → PROPOSER_ROLE  to Governor
 *   b. Grant Timelock → EXECUTOR_ROLE  to address(0)  [anyone can execute]
 *   c. Revoke Timelock → TIMELOCK_ADMIN_ROLE from deployer (self-administered)
 *   d. Grant Treasury → EXECUTOR_ROLE  to Timelock
 *   e. Grant Treasury → GUARDIAN_ROLE  to Owner (already granted in constructor)
 *
 * After deployment, the deployer should transfer the NGTT token's Ownable
 * ownership to the Timelock address so all administrative minting is
 * gated behind governance.
 *
 * Security notes:
 *   - Never hard-code private keys in this file.
 *   - Verify all emitted event addresses after deployment.
 *   - Use a hardware wallet or multi-sig for mainnet deployment.
 *   - Confirm contract bytecode on Etherscan before transferring ownership.
 */

"use strict";

const { ethers } = require("hardhat");

// ---------------------------------------------------------------------------
// Governance parameters
// ---------------------------------------------------------------------------
const TIMELOCK_MIN_DELAY = 2 * 24 * 60 * 60; // 2 days in seconds

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function log(label, address) {
  console.log(`  ✅  ${label.padEnd(30)} ${address}`);
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
async function main() {
  const [deployer] = await ethers.getSigners();
  const ownerAddress = process.env.OWNER_ADDRESS || deployer.address;

  console.log("\n═══════════════════════════════════════════════════════════");
  console.log("  Nexus Protocol DAO — Deployment Script");
  console.log("═══════════════════════════════════════════════════════════");
  console.log(`  Network    : ${(await ethers.provider.getNetwork()).name}`);
  console.log(`  Deployer   : ${deployer.address}`);
  console.log(`  Owner      : ${ownerAddress}`);
  console.log(`  Balance    : ${ethers.utils.formatEther(await deployer.getBalance())} ETH`);
  console.log("═══════════════════════════════════════════════════════════\n");

  // ── Step 1: NGTTGovernanceToken ──────────────────────────────────────────
  console.log("Step 1: Deploying NGTTGovernanceToken …");
  const NGTTFactory = await ethers.getContractFactory("NGTTGovernanceToken");
  const ngtt = await NGTTFactory.deploy();
  await ngtt.deployed();
  log("NGTTGovernanceToken", ngtt.address);

  // ── Step 2: NexusDAOTimelock ─────────────────────────────────────────────
  // Proposers and executors are set after the Governor is deployed (step 3).
  // We use empty arrays here and grant roles in the ceremony (step 5).
  console.log("\nStep 2: Deploying NexusDAOTimelock …");
  const TimelockFactory = await ethers.getContractFactory("NexusDAOTimelock");
  const timelock = await TimelockFactory.deploy(
    TIMELOCK_MIN_DELAY,
    [],              // proposers — will be set to [governor] in ceremony
    [],              // executors — will be set to [address(0)] in ceremony
    deployer.address // initial admin — renounced in ceremony
  );
  await timelock.deployed();
  log("NexusDAOTimelock", timelock.address);
  log("  Min delay (s)", TIMELOCK_MIN_DELAY.toString());

  // ── Step 3: NexusDAOGovernor ─────────────────────────────────────────────
  console.log("\nStep 3: Deploying NexusDAOGovernor …");
  const GovernorFactory = await ethers.getContractFactory("NexusDAOGovernor");
  const governor = await GovernorFactory.deploy(ngtt.address, timelock.address);
  await governor.deployed();
  log("NexusDAOGovernor", governor.address);
  log("  Voting delay (blocks)", (await governor.votingDelay()).toString());
  log("  Voting period (blocks)", (await governor.votingPeriod()).toString());
  log("  Proposal threshold", ethers.utils.formatEther(await governor.proposalThreshold()) + " NGTT");
  log("  Quorum numerator", (await governor.quorumNumerator()).toString() + "%");

  // ── Step 4: NexusDAOTreasury ─────────────────────────────────────────────
  console.log("\nStep 4: Deploying NexusDAOTreasury …");
  const TreasuryFactory = await ethers.getContractFactory("NexusDAOTreasury");
  const treasury = await TreasuryFactory.deploy(ownerAddress);
  await treasury.deployed();
  log("NexusDAOTreasury", treasury.address);

  // ── Step 5: Role assignment ceremony ────────────────────────────────────
  console.log("\nStep 5: Role assignment ceremony …");

  const PROPOSER_ROLE   = await timelock.PROPOSER_ROLE();
  const EXECUTOR_ROLE   = await timelock.EXECUTOR_ROLE();
  const CANCELLER_ROLE  = await timelock.CANCELLER_ROLE();
  const ADMIN_ROLE      = await timelock.TIMELOCK_ADMIN_ROLE();
  const TREASURY_EXEC   = await treasury.EXECUTOR_ROLE();
  const GUARDIAN_ROLE   = await treasury.GUARDIAN_ROLE();

  // 5a. Grant Governor PROPOSER_ROLE on Timelock
  let tx = await timelock.grantRole(PROPOSER_ROLE, governor.address);
  await tx.wait();
  log("  Timelock PROPOSER_ROLE → Governor", governor.address);

  // 5b. Grant address(0) EXECUTOR_ROLE on Timelock (anyone can execute)
  tx = await timelock.grantRole(EXECUTOR_ROLE, ethers.constants.AddressZero);
  await tx.wait();
  log("  Timelock EXECUTOR_ROLE → address(0)", "(public execution)");

  // 5c. Grant CANCELLER_ROLE to Owner for emergency veto
  if (ownerAddress !== deployer.address) {
    tx = await timelock.grantRole(CANCELLER_ROLE, ownerAddress);
    await tx.wait();
    log("  Timelock CANCELLER_ROLE → Owner", ownerAddress);
  }

  // 5d. Grant Timelock EXECUTOR_ROLE on Treasury
  tx = await treasury.grantRole(TREASURY_EXEC, timelock.address);
  await tx.wait();
  log("  Treasury EXECUTOR_ROLE → Timelock", timelock.address);

  // 5e. Revoke deployer TIMELOCK_ADMIN_ROLE (timelock becomes self-administered)
  tx = await timelock.revokeRole(ADMIN_ROLE, deployer.address);
  await tx.wait();
  log("  Timelock ADMIN_ROLE revoked from deployer", deployer.address);

  // 5f. Transfer NGTT ownership to Timelock (all owner-only NGTT calls via governance)
  tx = await ngtt.transferOwnership(timelock.address);
  await tx.wait();
  log("  NGTT ownership transferred → Timelock", timelock.address);

  // ── Summary ──────────────────────────────────────────────────────────────
  console.log("\n═══════════════════════════════════════════════════════════");
  console.log("  Deployment complete — save these addresses:");
  console.log("═══════════════════════════════════════════════════════════");
  console.log(JSON.stringify({
    network:              (await ethers.provider.getNetwork()).name,
    NGTTGovernanceToken:  ngtt.address,
    NexusDAOTimelock:     timelock.address,
    NexusDAOGovernor:     governor.address,
    NexusDAOTreasury:     treasury.address,
  }, null, 2));
  console.log("═══════════════════════════════════════════════════════════\n");

  console.log("⚠️  Next steps:");
  console.log("   1. Verify contracts on Etherscan.");
  console.log("   2. Update governance.html with live contract addresses.");
  console.log("   3. Announce to NGTT holders: call delegate(yourAddress) to activate votes.");
  console.log("   4. Submit first governance proposal via the DAO frontend.");
  console.log("   5. Confirm GUARDIAN_ROLE is held by Owner + all Super Delegates.\n");
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
