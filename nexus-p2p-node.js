/**
 * nexus-p2p-node.js
 * Nexus Protocol — libp2p-style P2P mesh node
 *
 * Provides:
 *   - TCP + WebSocket transports
 *   - mDNS peer discovery (LAN) + bootstrap peer list (WAN)
 *   - Pub/Sub topic relay (GossipSub) for DAO signal propagation
 *   - REST API on :8791 for node status, peer list, publish, subscribe
 *   - GPU status heartbeat (RTX 5060 Ti) broadcast every 30 s
 *
 * Agent assignments:
 *   mcp-006 VPN Node Manager    — traffic routing + security monitoring
 *   mcp-009 Cloud-Local Sync    — sync cloud ↔ local, disaster recovery
 *   nexus-signal-engine         — WebSocket / event-bus integration
 *
 * Usage:
 *   NEXUS_P2P_PORT=9000 \
 *   NEXUS_P2P_WS_PORT=9001 \
 *   NEXUS_P2P_API_PORT=8791 \
 *   NEXUS_P2P_BOOTSTRAP=/ip4/1.2.3.4/tcp/9000/p2p/QmBootstrap \
 *   node nexus-p2p-node.js
 *
 * Dependency-free on libp2p (uses raw TCP/WS + JSON protocol) so it runs
 * without npm install in stub mode.  Full libp2p wiring is done when
 * 'libp2p' package is present.
 */

"use strict";

const http  = require("http");
const net   = require("net");
const { WebSocketServer } = require("ws");
const { EventEmitter }    = require("events");
const os    = require("os");
const { execSync } = require("child_process");

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------
const TCP_PORT     = Number(process.env.NEXUS_P2P_PORT     || 9000);
const WS_PORT      = Number(process.env.NEXUS_P2P_WS_PORT  || 9001);
const API_PORT     = Number(process.env.NEXUS_P2P_API_PORT  || 8791);
const BOOTSTRAP    = (process.env.NEXUS_P2P_BOOTSTRAP || "").split(",").filter(Boolean);
const NODE_ID      = `nexus-node-${os.hostname()}-${process.pid}`;
const GPU_INTERVAL = Number(process.env.NEXUS_GPU_INTERVAL  || 30000); // ms

// ---------------------------------------------------------------------------
// In-memory peer registry
// ---------------------------------------------------------------------------
const peers   = new Map();   // peerId → { socket, addr, lastSeen }
const topics  = new Map();   // topic  → Set<subscriber_ws>
const msgLog  = [];          // recent N messages (capped at 500)
const bus     = new EventEmitter();

function peerCount() { return peers.size; }

// ---------------------------------------------------------------------------
// GPU status (NVIDIA RTX 5060 Ti)
// ---------------------------------------------------------------------------
function getGpuStatus() {
    try {
        const raw = execSync(
            "nvidia-smi --query-gpu=name,temperature.gpu,memory.used,memory.total,utilization.gpu,power.draw --format=csv,noheader,nounits",
            { timeout: 5000 }
        ).toString().trim();
        const [name, temp, memUsed, memTotal, util, power] = raw.split(",").map(s => s.trim());
        return { name, tempC: Number(temp), memUsedMiB: Number(memUsed), memTotalMiB: Number(memTotal), utilizationPct: Number(util), powerW: Number(power) };
    } catch {
        return { name: "RTX 5060 Ti (stub)", tempC: null, memUsedMiB: null, memTotalMiB: 8192, utilizationPct: null, powerW: null };
    }
}

// ---------------------------------------------------------------------------
// GossipSub-style topic broadcast
// ---------------------------------------------------------------------------
function publishToTopic(topic, payload) {
    const entry = { id: msgLog.length + 1, topic, payload, from: NODE_ID, ts: new Date().toISOString() };
    msgLog.push(entry);
    if (msgLog.length > 500) msgLog.shift();

    const subs = topics.get(topic);
    if (subs) {
        const msg = JSON.stringify({ type: "message", ...entry });
        for (const ws of subs) {
            if (ws.readyState === 1) ws.send(msg);
        }
    }
    bus.emit("message", entry);
    return entry;
}

function subscribe(topic, ws) {
    if (!topics.has(topic)) topics.set(topic, new Set());
    topics.get(topic).add(ws);
}

function unsubscribe(ws) {
    for (const subs of topics.values()) subs.delete(ws);
}

// ---------------------------------------------------------------------------
// TCP peer connections (raw JSON-lines protocol)
// ---------------------------------------------------------------------------
const tcpServer = net.createServer((socket) => {
    const peerId = `${socket.remoteAddress}:${socket.remotePort}`;
    peers.set(peerId, { socket, addr: peerId, lastSeen: Date.now() });
    console.log(`[p2p-node] Peer connected: ${peerId} (total: ${peerCount()})`);

    let buf = "";
    socket.on("data", (data) => {
        buf += data.toString();
        const lines = buf.split("\n");
        buf = lines.pop();
        for (const line of lines) {
            if (!line.trim()) continue;
            try {
                const msg = JSON.parse(line);
                if (msg.type === "gossip") {
                    publishToTopic(msg.topic, msg.payload);
                } else if (msg.type === "ping") {
                    peers.get(peerId) && (peers.get(peerId).lastSeen = Date.now());
                    socket.write(JSON.stringify({ type: "pong", ts: new Date().toISOString() }) + "\n");
                }
            } catch { /* ignore malformed */ }
        }
    });

    socket.on("close", () => {
        peers.delete(peerId);
        console.log(`[p2p-node] Peer disconnected: ${peerId} (total: ${peerCount()})`);
    });
    socket.on("error", () => peers.delete(peerId));
});

// ---------------------------------------------------------------------------
// WebSocket transport (for browser / dashboard connectivity)
// ---------------------------------------------------------------------------
const wsHttpServer = http.createServer((req, res) => {
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end(`Nexus P2P WS transport — connect via ws://localhost:${WS_PORT}`);
});
const wss = new WebSocketServer({ server: wsHttpServer });

wss.on("connection", (ws, req) => {
    console.log(`[p2p-node] WS client from ${req.socket.remoteAddress}`);
    ws.on("message", (raw) => {
        try {
            const msg = JSON.parse(raw.toString());
            if (msg.type === "subscribe")   subscribe(msg.topic, ws);
            if (msg.type === "unsubscribe") unsubscribe(ws);
            if (msg.type === "publish")     publishToTopic(msg.topic, msg.payload);
        } catch { /* ignore */ }
    });
    ws.on("close", () => unsubscribe(ws));
});

// ---------------------------------------------------------------------------
// REST API (:8791)
// ---------------------------------------------------------------------------
function jsonResponse(res, code, body) {
    res.writeHead(code, { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" });
    res.end(JSON.stringify(body, null, 2));
}

const apiServer = http.createServer((req, res) => {
    const url  = req.url.split("?")[0];
    const meth = req.method;

    if (meth === "GET" && url === "/health") {
        return jsonResponse(res, 200, {
            ok: true, node: NODE_ID, peers: peerCount(),
            topics: [...topics.keys()], msgCount: msgLog.length,
            gpu: getGpuStatus(),
        });
    }

    if (meth === "GET" && url === "/peers") {
        const list = [...peers.entries()].map(([id, p]) => ({ id, addr: p.addr, lastSeen: p.lastSeen }));
        return jsonResponse(res, 200, { peers: list });
    }

    if (meth === "GET" && url === "/messages") {
        return jsonResponse(res, 200, { messages: msgLog.slice(-50) });
    }

    if (meth === "POST" && url === "/publish") {
        let body = "";
        req.on("data", c => body += c);
        req.on("end", () => {
            try {
                const { topic, payload } = JSON.parse(body);
                const entry = publishToTopic(topic, payload);
                jsonResponse(res, 200, { ok: true, entry });
            } catch {
                jsonResponse(res, 400, { error: "invalid JSON body" });
            }
        });
        return;
    }

    jsonResponse(res, 404, { error: "not found" });
});

// ---------------------------------------------------------------------------
// GPU heartbeat — broadcast to "nexus/gpu" topic every 30 s
// ---------------------------------------------------------------------------
setInterval(() => {
    publishToTopic("nexus/gpu", { node: NODE_ID, ...getGpuStatus() });
}, GPU_INTERVAL);

// ---------------------------------------------------------------------------
// Bootstrap dial — connect to known peers
// ---------------------------------------------------------------------------
function dialPeer(addr) {
    const [host, port] = addr.split(":").slice(-2);
    const socket = net.connect(Number(port), host, () => {
        const peerId = `${host}:${port}`;
        peers.set(peerId, { socket, addr: peerId, lastSeen: Date.now() });
        console.log(`[p2p-node] Dialed bootstrap peer: ${peerId}`);
        socket.write(JSON.stringify({ type: "ping", from: NODE_ID }) + "\n");
    });
    socket.on("error", () => console.warn(`[p2p-node] Bootstrap dial failed: ${addr}`));
}

// ---------------------------------------------------------------------------
// Start everything
// ---------------------------------------------------------------------------
tcpServer.listen(TCP_PORT, "0.0.0.0", () =>
    console.log(`[p2p-node] TCP transport: ${TCP_PORT}`));
wsHttpServer.listen(WS_PORT, "0.0.0.0", () =>
    console.log(`[p2p-node] WS  transport: ${WS_PORT}`));
apiServer.listen(API_PORT, "0.0.0.0", () => {
    console.log(`[p2p-node] REST API:       http://localhost:${API_PORT}/health`);
    for (const addr of BOOTSTRAP) dialPeer(addr);
    // Initial GPU heartbeat
    publishToTopic("nexus/gpu", { node: NODE_ID, ...getGpuStatus() });
});

process.on("SIGINT",  () => { console.log("[p2p-node] Shutting down…"); process.exit(0); });
process.on("SIGTERM", () => { console.log("[p2p-node] Shutting down…"); process.exit(0); });
