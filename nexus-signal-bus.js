/**
 * Nexus Protocol — Signal Bus
 *
 * Subscribes to on-chain events from all deployed Nexus contracts using
 * ethers.js and re-broadcasts them over a local WebSocket server so that
 * dashboard and governance UI pages can receive live updates without polling.
 *
 * Architecture:
 *   [Ethereum node / RPC]
 *       │ ethers.js event listeners
 *       ▼
 *   NexusSignalBus  (this file, runs as Node.js process)
 *       │ WebSocket broadcast
 *       ▼
 *   dashboard.html, governance.html, financial-ops-dashboard.html
 *
 * Usage:
 *   NEXUS_RPC_URL=wss://mainnet.infura.io/ws/v3/YOUR_KEY \
 *   NEXUS_GOVERNOR_ADDRESS=0x... \
 *   NEXUS_TREASURY_ADDRESS=0x... \
 *   NEXUS_TOKEN_ADDRESS=0x... \
 *   NEXUS_SIGNAL_BUS_PORT=8790 \
 *   node nexus-signal-bus.js
 *
 * All environment variables are optional — the bus will start in stub mode
 * (no contract subscriptions) if RPC_URL is not set, and still serve the
 * WebSocket endpoint for dashboard connectivity tests.
 */

"use strict";

const http = require("http");
const { WebSocketServer } = require("ws");
const { ethers } = require("ethers");

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------
const RPC_URL = String(process.env.NEXUS_RPC_URL || "").trim();
const GOVERNOR_ADDRESS = String(process.env.NEXUS_GOVERNOR_ADDRESS || "").trim();
const TREASURY_ADDRESS = String(process.env.NEXUS_TREASURY_ADDRESS || "").trim();
const TOKEN_ADDRESS = String(process.env.NEXUS_TOKEN_ADDRESS || "").trim();
const LP_STAKING_ADDRESS = String(process.env.NEXUS_LP_STAKING_ADDRESS || "").trim();
const RWA_ADDRESS = String(process.env.NEXUS_RWA_ADDRESS || "").trim();
const FRACTAL_VAULT_ADDRESS = String(process.env.NEXUS_FRACTAL_VAULT_ADDRESS || "").trim();
const PORT = Number(process.env.NEXUS_SIGNAL_BUS_PORT || 8790);
const PUBLIC_ORIGIN = String(process.env.NEXUS_SIGNAL_BUS_ORIGIN || "*").trim();

// ---------------------------------------------------------------------------
// Minimal ABIs (event signatures only)
// ---------------------------------------------------------------------------
const GOVERNOR_ABI = [
    "event ProposalCreated(uint256 proposalId, address proposer, address[] targets, uint256[] values, string[] signatures, bytes[] calldatas, uint256 startBlock, uint256 endBlock, string description)",
    "event VoteCast(address indexed voter, uint256 proposalId, uint8 support, uint256 weight, string reason)",
    "event ProposalExecuted(uint256 proposalId)",
    "event ProposalCanceled(uint256 proposalId)",
    "event ProposalQueued(uint256 proposalId, uint256 eta)",
];

const TREASURY_ABI = [
    "event ETHDeposited(address indexed sender, uint256 amount)",
    "event ETHTransferred(address indexed recipient, uint256 amount, string reason)",
    "event ERC20Deposited(address indexed token, address indexed sender, uint256 amount)",
    "event ERC20Transferred(address indexed token, address indexed recipient, uint256 amount, string reason)",
    "event TreasuryPaused(address indexed guardian)",
    "event TreasuryUnpaused(address indexed guardian)",
    "event LargeETHTransferRequested(uint256 indexed nonce, address indexed recipient, uint256 amount, address requestedBy)",
    "event LargeETHTransferConfirmed(uint256 indexed nonce, address indexed confirmedBy)",
    "event LargeETHTransferExecuted(uint256 indexed nonce, address indexed recipient, uint256 amount)",
];

const TOKEN_ABI = [
    "event Transfer(address indexed from, address indexed to, uint256 value)",
    "event DelegateChanged(address indexed delegator, address indexed fromDelegate, address indexed toDelegate)",
    "event DelegateVotesChanged(address indexed delegate, uint256 previousBalance, uint256 newBalance)",
    "event GameCompleted(address indexed player, uint256 reward, uint256 skillIncrease)",
    "event ProfitDistributed(address indexed recipient, uint256 amount)",
];

const LP_STAKING_ABI = [
    "event Deposited(address indexed user, uint256 amount)",
    "event Withdrawn(address indexed user, uint256 amount)",
    "event RewardClaimed(address indexed user, uint256 reward)",
    "event RewardRateUpdated(uint256 oldRate, uint256 newRate)",
];

const RWA_ABI = [
    "event AssetMinted(uint256 indexed tokenId, address indexed owner, bytes32 titleHash, string documentCid, string propertyAddress)",
    "event ValuationUpdated(uint256 indexed tokenId, uint256 newValueUsdCents)",
    "event RentUpdated(uint256 indexed tokenId, uint256 newAnnualRentUsdCents)",
    "event AssetFractionalised(uint256 indexed tokenId, address fractionContract)",
];

const FRACTAL_VAULT_ABI = [
    "event Deposited(address indexed user, uint256 assets, uint256 shares)",
    "event Redeemed(address indexed user, uint256 shares, uint256 assets)",
    "event HarvestReinvested(uint256 indexed cycle, uint256 yieldAmount, uint256 reinvestedAmount, uint256 newTotalAssets)",
];

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
/** @type {Set<import('ws').WebSocket>} */
const clients = new Set();
let eventCount = 0;

// ---------------------------------------------------------------------------
// WebSocket broadcast
// ---------------------------------------------------------------------------
function broadcast(event) {
    const payload = JSON.stringify(event);
    for (const client of clients) {
        if (client.readyState === 1 /* OPEN */) {
            client.send(payload);
        }
    }
}

function emitSignal(source, eventName, data) {
    eventCount++;
    const signal = {
        id: eventCount,
        source,
        event: eventName,
        data,
        timestamp: new Date().toISOString(),
    };
    console.log(`[signal-bus] ${source}:${eventName}`, JSON.stringify(data));
    broadcast(signal);
    return signal;
}

// ---------------------------------------------------------------------------
// Contract subscriptions
// ---------------------------------------------------------------------------
function subscribeGovernor(provider) {
    if (!ethers.utils.isAddress(GOVERNOR_ADDRESS)) return;
    const contract = new ethers.Contract(GOVERNOR_ADDRESS, GOVERNOR_ABI, provider);

    contract.on("ProposalCreated", (proposalId, proposer, targets, values, signatures, calldatas, startBlock, endBlock, description) => {
        emitSignal("governor", "ProposalCreated", { proposalId: proposalId.toString(), proposer, startBlock: startBlock.toString(), endBlock: endBlock.toString(), description });
    });
    contract.on("VoteCast", (voter, proposalId, support, weight, reason) => {
        emitSignal("governor", "VoteCast", { voter, proposalId: proposalId.toString(), support, weight: weight.toString(), reason });
    });
    contract.on("ProposalExecuted", (proposalId) => {
        emitSignal("governor", "ProposalExecuted", { proposalId: proposalId.toString() });
    });
    contract.on("ProposalCanceled", (proposalId) => {
        emitSignal("governor", "ProposalCanceled", { proposalId: proposalId.toString() });
    });
    contract.on("ProposalQueued", (proposalId, eta) => {
        emitSignal("governor", "ProposalQueued", { proposalId: proposalId.toString(), eta: eta.toString() });
    });

    console.log(`[signal-bus] Subscribed to Governor at ${GOVERNOR_ADDRESS}`);
}

function subscribeTreasury(provider) {
    if (!ethers.utils.isAddress(TREASURY_ADDRESS)) return;
    const contract = new ethers.Contract(TREASURY_ADDRESS, TREASURY_ABI, provider);

    contract.on("ETHDeposited", (sender, amount) => {
        emitSignal("treasury", "ETHDeposited", { sender, amount: ethers.utils.formatEther(amount) + " ETH" });
    });
    contract.on("ETHTransferred", (recipient, amount, reason) => {
        emitSignal("treasury", "ETHTransferred", { recipient, amount: ethers.utils.formatEther(amount) + " ETH", reason });
    });
    contract.on("TreasuryPaused", (guardian) => {
        emitSignal("treasury", "TreasuryPaused", { guardian });
    });
    contract.on("TreasuryUnpaused", (guardian) => {
        emitSignal("treasury", "TreasuryUnpaused", { guardian });
    });
    contract.on("LargeETHTransferRequested", (nonce, recipient, amount, requestedBy) => {
        emitSignal("treasury", "LargeETHTransferRequested", { nonce: nonce.toString(), recipient, amount: ethers.utils.formatEther(amount) + " ETH", requestedBy });
    });
    contract.on("LargeETHTransferConfirmed", (nonce, confirmedBy) => {
        emitSignal("treasury", "LargeETHTransferConfirmed", { nonce: nonce.toString(), confirmedBy });
    });
    contract.on("LargeETHTransferExecuted", (nonce, recipient, amount) => {
        emitSignal("treasury", "LargeETHTransferExecuted", { nonce: nonce.toString(), recipient, amount: ethers.utils.formatEther(amount) + " ETH" });
    });

    console.log(`[signal-bus] Subscribed to Treasury at ${TREASURY_ADDRESS}`);
}

function subscribeToken(provider) {
    if (!ethers.utils.isAddress(TOKEN_ADDRESS)) return;
    const contract = new ethers.Contract(TOKEN_ADDRESS, TOKEN_ABI, provider);

    contract.on("GameCompleted", (player, reward, skillIncrease) => {
        emitSignal("token", "GameCompleted", { player, reward: ethers.utils.formatEther(reward) + " NGTT", skillIncrease: skillIncrease.toString() });
    });
    contract.on("ProfitDistributed", (recipient, amount) => {
        emitSignal("token", "ProfitDistributed", { recipient, amount: ethers.utils.formatEther(amount) + " NGTT" });
    });
    contract.on("DelegateChanged", (delegator, fromDelegate, toDelegate) => {
        emitSignal("token", "DelegateChanged", { delegator, fromDelegate, toDelegate });
    });

    console.log(`[signal-bus] Subscribed to Token at ${TOKEN_ADDRESS}`);
}

function subscribeLPStaking(provider) {
    if (!ethers.utils.isAddress(LP_STAKING_ADDRESS)) return;
    const contract = new ethers.Contract(LP_STAKING_ADDRESS, LP_STAKING_ABI, provider);

    contract.on("Deposited", (user, amount) => {
        emitSignal("lp-staking", "Deposited", { user, amount: ethers.utils.formatEther(amount) });
    });
    contract.on("RewardClaimed", (user, reward) => {
        emitSignal("lp-staking", "RewardClaimed", { user, reward: ethers.utils.formatEther(reward) + " NGTT" });
    });

    console.log(`[signal-bus] Subscribed to LPStaking at ${LP_STAKING_ADDRESS}`);
}

function subscribeRWA(provider) {
    if (!ethers.utils.isAddress(RWA_ADDRESS)) return;
    const contract = new ethers.Contract(RWA_ADDRESS, RWA_ABI, provider);

    contract.on("AssetMinted", (tokenId, owner, titleHash, documentCid, propertyAddress) => {
        emitSignal("rwa", "AssetMinted", { tokenId: tokenId.toString(), owner, propertyAddress });
    });
    contract.on("ValuationUpdated", (tokenId, newValueUsdCents) => {
        emitSignal("rwa", "ValuationUpdated", { tokenId: tokenId.toString(), valueUsd: (Number(newValueUsdCents) / 100).toFixed(2) });
    });

    console.log(`[signal-bus] Subscribed to RWA at ${RWA_ADDRESS}`);
}

function subscribeFractalVault(provider) {
    if (!ethers.utils.isAddress(FRACTAL_VAULT_ADDRESS)) return;
    const contract = new ethers.Contract(FRACTAL_VAULT_ADDRESS, FRACTAL_VAULT_ABI, provider);

    contract.on("Deposited", (user, assets, shares) => {
        emitSignal("fractal-vault", "Deposited", { user, assets: ethers.utils.formatEther(assets) + " NGTT", shares: ethers.utils.formatEther(shares) + " fNGTT" });
    });
    contract.on("HarvestReinvested", (cycle, yieldAmount, reinvestedAmount, newTotalAssets) => {
        emitSignal("fractal-vault", "HarvestReinvested", {
            cycle: cycle.toString(),
            yieldAmount: ethers.utils.formatEther(yieldAmount) + " NGTT",
            reinvestedAmount: ethers.utils.formatEther(reinvestedAmount) + " NGTT",
            newTotalAssets: ethers.utils.formatEther(newTotalAssets) + " NGTT",
        });
    });

    console.log(`[signal-bus] Subscribed to FractalVault at ${FRACTAL_VAULT_ADDRESS}`);
}

// ---------------------------------------------------------------------------
// HTTP health endpoint (also upgrades WebSocket connections)
// ---------------------------------------------------------------------------
function createHttpServer() {
    return http.createServer((req, res) => {
        if (req.method === "GET" && req.url === "/health") {
            res.writeHead(200, {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": PUBLIC_ORIGIN,
            });
            res.end(JSON.stringify({
                ok: true,
                service: "nexus-signal-bus",
                port: PORT,
                clients: clients.size,
                eventCount,
                rpcConnected: Boolean(RPC_URL),
                contracts: {
                    governor: GOVERNOR_ADDRESS || null,
                    treasury: TREASURY_ADDRESS || null,
                    token: TOKEN_ADDRESS || null,
                    lpStaking: LP_STAKING_ADDRESS || null,
                    rwa: RWA_ADDRESS || null,
                    fractalVault: FRACTAL_VAULT_ADDRESS || null,
                },
            }));
            return;
        }
        res.writeHead(404, { "Content-Type": "text/plain" });
        res.end("Not found. WebSocket endpoint: ws://localhost:" + PORT);
    });
}

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------
async function bootstrap() {
    const httpServer = createHttpServer();
    const wss = new WebSocketServer({ server: httpServer });

    wss.on("connection", (ws, req) => {
        const origin = req.headers.origin || "unknown";
        clients.add(ws);
        console.log(`[signal-bus] Client connected from ${origin} (total: ${clients.size})`);

        // Send a welcome / current-state message immediately
        ws.send(JSON.stringify({
            id: 0,
            source: "signal-bus",
            event: "connected",
            data: {
                service: "nexus-signal-bus",
                eventCount,
                contracts: {
                    governor: GOVERNOR_ADDRESS || null,
                    treasury: TREASURY_ADDRESS || null,
                    token: TOKEN_ADDRESS || null,
                },
            },
            timestamp: new Date().toISOString(),
        }));

        ws.on("close", () => {
            clients.delete(ws);
            console.log(`[signal-bus] Client disconnected (total: ${clients.size})`);
        });

        ws.on("error", (err) => {
            console.error("[signal-bus] WebSocket error:", err.message);
            clients.delete(ws);
        });
    });

    httpServer.listen(PORT, "0.0.0.0", async () => {
        console.log(`[signal-bus] Listening on ws://localhost:${PORT} and http://localhost:${PORT}/health`);

        if (RPC_URL) {
            try {
                const provider = new ethers.providers.WebSocketProvider(RPC_URL);
                provider.on("error", (err) => {
                    console.error("[signal-bus] Provider error:", err.message);
                });

                subscribeGovernor(provider);
                subscribeTreasury(provider);
                subscribeToken(provider);
                subscribeLPStaking(provider);
                subscribeRWA(provider);
                subscribeFractalVault(provider);

                console.log("[signal-bus] All contract subscriptions active.");
            } catch (err) {
                console.error("[signal-bus] Failed to connect to RPC:", err.message);
                console.warn("[signal-bus] Running in stub mode (no contract subscriptions).");
            }
        } else {
            console.warn("[signal-bus] NEXUS_RPC_URL not set — running in stub mode.");
        }
    });
}

bootstrap().catch((err) => {
    console.error("[signal-bus] Fatal startup error:", err);
    process.exitCode = 1;
});
