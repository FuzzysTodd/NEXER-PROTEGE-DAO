/**
 * nexus-signal-relay.js
 * Nexus Protocol — MCP Agent → WebSocket Signal Relay
 *
 * Bridges the local MCP tool bus to the live nexus-signal-bus WebSocket,
 * so that MIG network bots (mcp-001 … mcp-010) and financial-ops bots
 * (mcp-fin-011/012/013) can publish and consume on-chain signals without
 * connecting directly to the Ethereum RPC.
 *
 * Architecture:
 *   [MCP agent tools]
 *       │ REST POST /relay/publish
 *       ▼
 *   NexusSignalRelay  (this file, port 8792)
 *       │ WebSocket client → nexus-signal-bus (:8790)
 *       ▼
 *   All subscribed dashboard / governance UI pages
 *
 *   AND / OR
 *
 *   [nexus-signal-bus live events]
 *       │ WebSocket → relay
 *       ▼
 *   REST GET /relay/events  (polling endpoint for agents without WS support)
 *
 * Agent assignments (consumers):
 *   mcp-001 Game Theory Coordinator     — GameCompleted signals
 *   mcp-002 Token Economics Manager     — ProfitDistributed, Transfer
 *   mcp-003 DAO Governance Agent        — ProposalCreated, VoteCast, ProposalExecuted
 *   mcp-004 AI Data Pipeline Manager    — all events → GPU training feed
 *   mcp-010 Financial Analytics Agent   — ETHDeposited, ETHTransferred, LargeETH*
 *   mcp-fin-011 Pre-Error Bot           — error/alert events
 *   mcp-fin-012 Withdrawal Scanner      — ETHTransferred, ERC20Transferred
 *   mcp-fin-013 Success Reporter        — ProposalExecuted, HarvestReinvested
 *
 * Usage:
 *   NEXUS_SIGNAL_BUS_URL=ws://localhost:8790 \
 *   NEXUS_RELAY_PORT=8792 \
 *   node nexus-signal-relay.js
 */

"use strict";

const http  = require("http");
const ws_mod = require("ws");

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------
const BUS_URL    = process.env.NEXUS_SIGNAL_BUS_URL || "ws://localhost:8790";
const RELAY_PORT = Number(process.env.NEXUS_RELAY_PORT || 8792);
const MAX_EVENTS = 1000; // ring-buffer cap

// ---------------------------------------------------------------------------
// Ring-buffer of received events (for polling agents)
// ---------------------------------------------------------------------------
const eventRing = [];
let   eventSeq  = 0;

function pushEvent(evt) {
    eventSeq++;
    evt._seq = eventSeq;
    eventRing.push(evt);
    if (eventRing.length > MAX_EVENTS) eventRing.shift();
}

// ---------------------------------------------------------------------------
// Per-topic filter map (agent subscriptions via REST)
// ---------------------------------------------------------------------------
// topic → Set<{res, lastSeq}>
const agentSubs = new Map();

function broadcastToAgents(evt) {
    const topic = `${evt.source}:${evt.event}`;
    const subs  = agentSubs.get(topic) || agentSubs.get("*");
    if (!subs) return;
    const payload = JSON.stringify(evt) + "\n";
    for (const sub of [...subs]) {
        try { sub.res.write(payload); } catch { subs.delete(sub); }
    }
}

// ---------------------------------------------------------------------------
// WebSocket connection to nexus-signal-bus
// ---------------------------------------------------------------------------
let busSocket   = null;
let busConnected = false;
let reconnectTimer = null;

function connectToBus() {
    if (busSocket) { try { busSocket.terminate(); } catch {} }

    console.log(`[relay] Connecting to signal-bus at ${BUS_URL}…`);
    busSocket = new ws_mod.WebSocket(BUS_URL);

    busSocket.on("open", () => {
        busConnected = true;
        clearTimeout(reconnectTimer);
        console.log("[relay] Connected to nexus-signal-bus ✓");
    });

    busSocket.on("message", (raw) => {
        try {
            const evt = JSON.parse(raw.toString());
            pushEvent(evt);
            broadcastToAgents(evt);
        } catch { /* ignore malformed */ }
    });

    busSocket.on("close", () => {
        busConnected = false;
        console.warn("[relay] signal-bus connection closed — reconnecting in 5 s…");
        reconnectTimer = setTimeout(connectToBus, 5000);
    });

    busSocket.on("error", (err) => {
        busConnected = false;
        console.error("[relay] signal-bus error:", err.message);
        reconnectTimer = setTimeout(connectToBus, 5000);
    });
}

// ---------------------------------------------------------------------------
// REST API for MCP agents
// ---------------------------------------------------------------------------
function jsonResp(res, code, body) {
    res.writeHead(code, { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" });
    res.end(JSON.stringify(body, null, 2));
}

const server = http.createServer((req, res) => {
    const url  = req.url.split("?")[0];
    const meth = req.method;
    const qs   = Object.fromEntries(new URLSearchParams(req.url.split("?")[1] || ""));

    // ------------------------------------------------------------------
    // Health
    // ------------------------------------------------------------------
    if (meth === "GET" && url === "/health") {
        return jsonResp(res, 200, {
            ok: true, service: "nexus-signal-relay",
            busConnected, relayPort: RELAY_PORT,
            eventCount: eventSeq, buffered: eventRing.length,
        });
    }

    // ------------------------------------------------------------------
    // Publish — agent → signal-bus
    // ------------------------------------------------------------------
    if (meth === "POST" && url === "/relay/publish") {
        let body = "";
        req.on("data", c => body += c);
        req.on("end", () => {
            try {
                const evt = JSON.parse(body);
                if (busConnected && busSocket.readyState === 1) {
                    busSocket.send(JSON.stringify(evt));
                    return jsonResp(res, 200, { ok: true, forwarded: true });
                }
                // Buffer locally if bus is down
                pushEvent({ ...evt, _relayBuffered: true });
                return jsonResp(res, 200, { ok: true, forwarded: false, buffered: true });
            } catch {
                return jsonResp(res, 400, { error: "invalid JSON body" });
            }
        });
        return;
    }

    // ------------------------------------------------------------------
    // Poll events — agents pull recent events since a sequence number
    // ------------------------------------------------------------------
    if (meth === "GET" && url === "/relay/events") {
        const since = Number(qs.since || 0);
        const limit = Math.min(Number(qs.limit || 100), 500);
        const events = eventRing.filter(e => e._seq > since).slice(-limit);
        return jsonResp(res, 200, { events, lastSeq: eventSeq });
    }

    // ------------------------------------------------------------------
    // SSE stream — agents subscribe to a topic via Server-Sent Events
    // ------------------------------------------------------------------
    if (meth === "GET" && url === "/relay/stream") {
        const topic = qs.topic || "*";
        res.writeHead(200, {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            Connection: "keep-alive",
            "Access-Control-Allow-Origin": "*",
        });
        res.write(`data: ${JSON.stringify({ connected: true, topic })}\n\n`);

        const sub = { res };
        if (!agentSubs.has(topic)) agentSubs.set(topic, new Set());
        agentSubs.get(topic).add(sub);

        req.on("close", () => {
            agentSubs.get(topic) && agentSubs.get(topic).delete(sub);
        });
        return;
    }

    // ------------------------------------------------------------------
    // Agent registry — list which MIG agents are active consumers
    // ------------------------------------------------------------------
    if (meth === "GET" && url === "/relay/agents") {
        return jsonResp(res, 200, {
            agents: [
                { id: "mcp-001", role: "Game Theory Coordinator",   topics: ["token:GameCompleted"] },
                { id: "mcp-002", role: "Token Economics Manager",   topics: ["token:ProfitDistributed", "token:Transfer"] },
                { id: "mcp-003", role: "DAO Governance Agent",      topics: ["governor:ProposalCreated", "governor:VoteCast", "governor:ProposalExecuted"] },
                { id: "mcp-004", role: "AI Data Pipeline Manager",  topics: ["*"] },
                { id: "mcp-010", role: "Financial Analytics Agent", topics: ["treasury:ETHDeposited", "treasury:ETHTransferred", "treasury:LargeETHTransferRequested"] },
                { id: "mcp-fin-011", role: "Pre-Error Bot",         topics: ["signal-bus:connected"] },
                { id: "mcp-fin-012", role: "Withdrawal Scanner",    topics: ["treasury:ETHTransferred", "treasury:ERC20Transferred"] },
                { id: "mcp-fin-013", role: "Success Reporter",      topics: ["governor:ProposalExecuted", "fractal-vault:HarvestReinvested"] },
            ],
        });
    }

    jsonResp(res, 404, { error: "not found" });
});

// ---------------------------------------------------------------------------
// Start
// ---------------------------------------------------------------------------
server.listen(RELAY_PORT, "0.0.0.0", () => {
    console.log(`[relay] REST API: http://localhost:${RELAY_PORT}/health`);
    console.log(`[relay] SSE stream: http://localhost:${RELAY_PORT}/relay/stream?topic=*`);
    connectToBus();
});

process.on("SIGINT",  () => { console.log("[relay] Shutting down…"); process.exit(0); });
process.on("SIGTERM", () => { console.log("[relay] Shutting down…"); process.exit(0); });
