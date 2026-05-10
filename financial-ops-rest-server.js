const http = require("http");
const fs = require("fs");
const fsp = fs.promises;
const path = require("path");
const { URL } = require("url");

const PORT = Number(process.env.FINANCIAL_OPS_REST_PORT || 8788);
const ROOT = __dirname;
const REPORT_PATH = path.join(ROOT, "ops", "reports", "financial-ops-report.json");
const SOURCE_URL = String(process.env.FINANCIAL_OPS_SOURCE_URL || "").trim();
const SOURCE_KIND = String(process.env.FINANCIAL_OPS_SOURCE_KIND || "auto").trim().toLowerCase();
const DEFAULT_WALLET_ADDRESS = "0x33ffc308e693a5b49e0ee0241f41f03ccef495f2";
const LIVE_WALLET_ADDRESS = String(process.env.FINANCIAL_OPS_WALLET_ADDRESS || DEFAULT_WALLET_ADDRESS).trim();
const PUBLIC_ORIGIN = process.env.FINANCIAL_OPS_PUBLIC_ORIGIN || "*";

// ─────────────────────────────────────────────────────────────────────────────
// Expert Component Registry
// ─────────────────────────────────────────────────────────────────────────────
// Static manifest of the 10 Nexus code-space components and their expert
// domain, share weight, and registered handle.  Exposed read-only in the
// /api/v1/builder-fund/stats response so dashboards and Chainlink Automation
// upkeeps can correlate on-chain builder IDs with code-space attribution.
// ─────────────────────────────────────────────────────────────────────────────
const EXPERT_COMPONENTS = [
  { handle: "nexus-solidity-defi-expert",      component: "Solidity-DeFi-Core",             shares: 200, codeSpace: "contracts/NexusBuilderFund.sol"     },
  { handle: "nexus-lp-staking-expert",         component: "Solidity-AMM-Staking",           shares: 150, codeSpace: "contracts/NexusLPStaking.sol"        },
  { handle: "nexus-rwa-compliance-expert",     component: "Solidity-RWA-Compliance",        shares: 150, codeSpace: "contracts/NexusRWA.sol"              },
  { handle: "nexus-nft-fractionalize-expert",  component: "Solidity-NFT-Fractionalization", shares: 120, codeSpace: "contracts/NexusFractionalize.sol"    },
  { handle: "nexus-options-defi-expert",       component: "Solidity-Options-DeFi",          shares: 180, codeSpace: "contracts/NexusOptionsVault.sol"     },
  { handle: "nexus-vault-yield-expert",        component: "Solidity-Vault-Yield",           shares: 160, codeSpace: "contracts/NexusFractalVault.sol"     },
  { handle: "nexus-nodejs-infra-expert",       component: "NodeJS-WebSocket-Infra",         shares: 100, codeSpace: "nexus-signal-bus.js"                 },
  { handle: "nexus-python-qa-expert",          component: "Python-QA-Validation",           shares:  80, codeSpace: "nexus/e2e_soundness.py"             },
  { handle: "nexus-frontend-web3-expert",      component: "Frontend-Web3-UX",               shares:  90, codeSpace: "web3-interface.html"                 },
  { handle: "nexus-frontend-dapp-expert",      component: "Frontend-DApp-UX",               shares:  70, codeSpace: "builder-fund.html"                  },
];

// ─────────────────────────────────────────────────────────────────────────────
// Builder Fund Usage Tracker
// ─────────────────────────────────────────────────────────────────────────────
// In-process accumulator for API usage metrics.  These counters are:
//   1. Exposed read-only at GET /api/v1/builder-fund/stats for dashboards.
//   2. Submitted on-chain to NexusBuilderFund.sol via the ORACLE_ROLE wallet
//      (either manually or via a Chainlink Automation upkeep that polls /stats
//      and calls recordUsage() when the delta crosses a batch threshold).
//
// The contract address and oracle wallet are NOT embedded here — they are
// managed off-chain by the Chainlink Automation config or a cron job.
// This keeps the REST server stateless with respect to on-chain state.
// ─────────────────────────────────────────────────────────────────────────────
const builderFundUsage = (function () {
    const _counts = Object.create(null); // endpoint -> cumulative call count
    let _grandTotal = 0;
    const _startedAt = new Date().toISOString();

    return {
        /** Record one or more calls to an endpoint. */
        record(endpoint, count) {
            const n = (Number.isFinite(count) && count > 0) ? Math.floor(count) : 1;
            const key = String(endpoint || "unknown").trim();
            _counts[key] = (_counts[key] || 0) + n;
            _grandTotal += n;
        },
        /** Returns a plain-object snapshot suitable for JSON serialisation. */
        stats() {
            return {
                service: "nexus-builder-fund-usage",
                startedAt: _startedAt,
                snapshotAt: new Date().toISOString(),
                totalCalls: _grandTotal,
                byEndpoint: Object.assign(Object.create(null), _counts),
                builderFundContract: process.env.NEXUS_BUILDER_FUND_ADDRESS || null,
                placementWallet: process.env.NEXUS_PLACEMENT_WALLET || null,
                placementBps: (Number(process.env.NEXUS_PLACEMENT_BPS) || 0),
                ngttToken: process.env.NEXUS_NGTT_TOKEN_ADDRESS || null,
                ngttRewardPerEthWei: process.env.NEXUS_NGTT_REWARD_PER_ETH || null,
                expertRegistry: EXPERT_COMPONENTS,
                oracleNote: "Submit stats.byEndpoint to NexusBuilderFund.recordUsage() via ORACLE_ROLE.",
                feeNote: "Fee per call configured in NexusBuilderFund.feePerCallUsdCents.",
                placementNote: "placementBps of each deposit is auto-forwarded to placementWallet (dashboard/treasury wallet).",
                ngttNote: "ngttRewardPerEthWei NGTT tokens are awarded to builders per 1 ETH claimed.",
                expertRegistryNote: "expertRegistry lists the 10 Nexus code-space components, their expert domains, and share weights.",
            };
        },
    };
}());

function json(res, statusCode, payload, extraHeaders = {}) {
  res.writeHead(statusCode, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
    "Access-Control-Allow-Origin": PUBLIC_ORIGIN,
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    ...extraHeaders,
  });
  res.end(JSON.stringify(payload, null, 2));
}

function html(res, statusCode, body) {
  res.writeHead(statusCode, {
    "Content-Type": "text/html; charset=utf-8",
    "Cache-Control": "no-store",
    "Access-Control-Allow-Origin": PUBLIC_ORIGIN,
  });
  res.end(body);
}

function normalizeReport(report, source, metadata = {}) {
  const summary = report && report.summary ? report.summary : {};
  return {
    generatedAt: report && report.generatedAt ? report.generatedAt : new Date().toISOString(),
    source,
    sourceType: metadata.sourceType || (SOURCE_URL ? "upstream" : "local-file"),
    sourceUrl: SOURCE_URL || null,
    liveChain: metadata.liveChain || report.liveChain || null,
    summary: {
      filesScanned: Number(summary.filesScanned || 0),
      preErrorCount: Number(summary.preErrorCount || 0),
      withdrawSignalCount: Number(summary.withdrawSignalCount || 0),
      placementSignalCount: Number(summary.placementSignalCount || 0),
      approvalGate: summary.approvalGate || "required for any fund movement or treasury action",
    },
    bots: Array.isArray(report && report.bots) ? report.bots : [],
    preErrorFindings: Array.isArray(report && report.preErrorFindings) ? report.preErrorFindings : [],
    withdrawSignals: Array.isArray(report && report.withdrawSignals) ? report.withdrawSignals : [],
    placementSignals: Array.isArray(report && report.placementSignals) ? report.placementSignals : [],
    successLog: Array.isArray(report && report.successLog) ? report.successLog : [],
    recommendedActions: Array.isArray(report && report.recommendedActions) ? report.recommendedActions : [],
  };
}

function isRpcSource(sourceUrl) {
  if (!sourceUrl) {
    return false;
  }

  if (SOURCE_KIND === "rpc") {
    return true;
  }

  if (SOURCE_KIND === "report") {
    return false;
  }

  try {
    const parsed = new URL(sourceUrl);
    const host = parsed.hostname.toLowerCase();
    return host.includes("infura.io") || host.includes("alchemy") || host.includes("rpc");
  } catch (_) {
    return false;
  }
}

function formatUnits(hexValue, decimals) {
  if (!hexValue) {
    return null;
  }

  try {
    const value = BigInt(hexValue);
    const base = 10n ** BigInt(decimals);
    const whole = value / base;
    const fraction = (value % base).toString().padStart(decimals, "0").replace(/0+$/, "");
    return fraction ? `${whole.toString()}.${fraction}` : whole.toString();
  } catch (_) {
    return null;
  }
}

function hexToNumber(hexValue) {
  if (!hexValue) {
    return null;
  }

  try {
    return Number(BigInt(hexValue));
  } catch (_) {
    return null;
  }
}

function networkNameForChainId(chainId) {
  if (chainId === 1) {
    return "Ethereum Mainnet";
  }

  if (chainId === 5) {
    return "Goerli";
  }

  if (chainId === 11155111) {
    return "Sepolia";
  }

  if (chainId === 8453) {
    return "Base Mainnet";
  }

  if (chainId === 56) {
    return "BNB Smart Chain";
  }

  return chainId ? `Chain ${chainId}` : "Unknown network";
}

function formatCurrency(value) {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) {
    return null;
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(numericValue);
}

function formatDecimalAmount(amount, decimals) {
  const raw = String(amount ?? "").trim();
  if (!raw) {
    return null;
  }

  const negative = raw.startsWith("-");
  const digits = negative ? raw.slice(1) : raw;
  if (!/^\d+$/.test(digits)) {
    return null;
  }

  const numericDecimals = Number(decimals);
  if (!Number.isFinite(numericDecimals) || numericDecimals < 0) {
    return digits;
  }

  if (digits.length <= numericDecimals) {
    const fraction = digits.padStart(numericDecimals, "0").replace(/0+$/, "");
    const value = fraction ? `0.${fraction}` : "0";
    return negative && value !== "0" ? `-${value}` : value;
  }

  const whole = digits.slice(0, digits.length - numericDecimals);
  const fraction = digits.slice(-numericDecimals).replace(/0+$/, "");
  const value = fraction ? `${whole}.${fraction}` : whole;
  return negative && value !== "0" ? `-${value}` : value;
}

function isDuneSnapshotPayload(report) {
  return Boolean(
    report &&
    typeof report === "object" &&
    Array.isArray(report.balances) &&
    (report.wallet_address || report.walletAddress || report.request_time || report.response_time || report.next_offset)
  );
}

function normalizeDuneBalance(balance) {
  const numericValue = Number(balance.value_usd || 0);
  const normalizedAmount = formatDecimalAmount(balance.amount || "0", balance.decimals || 18);
  return {
    chain: balance.chain || "unknown",
    chainId: balance.chain_id || null,
    address: balance.address || "",
    amount: balance.amount || "0",
    amountDisplay: normalizedAmount,
    symbol: balance.symbol || "",
    name: balance.name || balance.symbol || "",
    decimals: Number.isFinite(Number(balance.decimals)) ? Number(balance.decimals) : 18,
    priceUsd: Number(balance.price_usd || 0),
    valueUsd: numericValue,
    valueUsdLabel: formatCurrency(numericValue),
    poolSize: Number(balance.pool_size || 0),
    lowLiquidity: Boolean(balance.low_liquidity),
    isNative: String(balance.address || "").toLowerCase() === "native",
  };
}

function summarizeDuneBalances(balances) {
  const summary = {
    balanceCount: balances.length,
    chainCount: 0,
    lowLiquidityCount: 0,
    highValueCount: 0,
    totalValueUsd: 0,
    nativeValueUsd: 0,
    chainBreakdown: {},
    topHoldings: [],
  };

  const chainNames = new Set();
  const orderedBalances = [...balances].sort((left, right) => right.valueUsd - left.valueUsd);

  for (const balance of balances) {
    summary.totalValueUsd += balance.valueUsd;
    if (balance.isNative) {
      summary.nativeValueUsd += balance.valueUsd;
    }
    if (balance.lowLiquidity) {
      summary.lowLiquidityCount += 1;
    }
    if (balance.valueUsd >= 1000) {
      summary.highValueCount += 1;
    }

    const chainKey = balance.chain || "unknown";
    chainNames.add(chainKey);
    summary.chainBreakdown[chainKey] = (summary.chainBreakdown[chainKey] || 0) + 1;
  }

  summary.chainCount = chainNames.size;
  summary.topHoldings = orderedBalances.slice(0, 5).map((balance) => ({
    chain: balance.chain,
    symbol: balance.symbol,
    name: balance.name,
    address: balance.address,
    valueUsd: balance.valueUsd,
    valueUsdLabel: balance.valueUsdLabel,
    lowLiquidity: balance.lowLiquidity,
  }));

  return summary;
}

function normalizeDuneReport(report, source) {
  const balances = Array.isArray(report && report.balances) ? report.balances.map(normalizeDuneBalance) : [];
  const stats = summarizeDuneBalances(balances);
  const walletAddress = String(report.wallet_address || report.walletAddress || "").trim();
  const requestTime = report.request_time || report.requestTime || "";
  const responseTime = report.response_time || report.responseTime || "";
  const generatedAt = responseTime || requestTime || new Date().toISOString();
  const lowLiquiditySymbols = balances.filter((balance) => balance.lowLiquidity).slice(0, 5).map((balance) => balance.symbol || balance.name || balance.address || "unknown");
  const highValueSymbols = [...balances].sort((left, right) => right.valueUsd - left.valueUsd).slice(0, 5).map((balance) => balance.symbol || balance.name || balance.address || "unknown");

  return {
    generatedAt,
    source,
    sourceType: "dune-snapshot",
    sourceUrl: SOURCE_URL || null,
    liveChain: {
      rpcMode: false,
      sourceKind: "dune",
      networkName: walletAddress ? "Dune Snapshot" : "Dune Portfolio Snapshot",
      chainId: null,
      blockNumber: null,
      blockHash: null,
      blockTimestamp: responseTime ? Math.floor(Date.parse(responseTime) / 1000) : null,
      blockTimestampIso: responseTime || generatedAt,
      gasPriceWei: null,
      gasPriceGwei: null,
      walletAddress: walletAddress || null,
      walletBalanceWei: null,
      walletBalanceEth: null,
      walletNonce: null,
      latestBlockTransactions: stats.balanceCount,
      portfolioValueUsd: stats.totalValueUsd,
      nativeValueUsd: stats.nativeValueUsd,
      balanceCount: stats.balanceCount,
      chainCount: stats.chainCount,
      lowLiquidityCount: stats.lowLiquidityCount,
      topHoldings: stats.topHoldings,
      requestTime: requestTime || null,
      responseTime: responseTime || null,
      nextOffset: report.next_offset || report.nextOffset || null,
    },
    summary: {
      filesScanned: stats.balanceCount,
      preErrorCount: 0,
      withdrawSignalCount: stats.lowLiquidityCount,
      placementSignalCount: stats.highValueCount,
      approvalGate: report.approvalGate || "required for any fund movement or treasury action",
    },
    bots: [
      {
        id: "dune-snapshot-001",
        name: "Dune Snapshot Normalizer",
        role: "Normalize portfolio balances, low-liquidity flags, and chain breakdowns from Dune exports.",
      },
    ],
    preErrorFindings: [],
    withdrawSignals: stats.lowLiquidityCount > 0 ? [
      {
        file: "dune://balances",
        count: stats.lowLiquidityCount,
        matches: lowLiquiditySymbols,
      },
    ] : [],
    placementSignals: stats.highValueCount > 0 ? [
      {
        file: "dune://portfolio",
        count: stats.highValueCount,
        matches: highValueSymbols,
      },
    ] : [],
    successLog: [
      {
        time: generatedAt,
        title: "Dune snapshot loaded",
        details: `${stats.balanceCount} balances across ${stats.chainCount} chains were normalized for wallet ${walletAddress || "unspecified"}.`,
        status: "success",
      },
    ],
    recommendedActions: [
      "Review low-liquidity holdings before routing any transfers.",
      "Use the balance breakdown to identify the largest positions by USD value.",
      "Keep settlement actions approval-gated even when the source is a Dune export.",
    ],
    balances,
    duneSnapshot: {
      walletAddress: walletAddress || null,
      requestTime: requestTime || null,
      responseTime: responseTime || null,
      nextOffset: report.next_offset || report.nextOffset || null,
      balanceCount: stats.balanceCount,
      chainCount: stats.chainCount,
      totalValueUsd: stats.totalValueUsd,
      nativeValueUsd: stats.nativeValueUsd,
      lowLiquidityCount: stats.lowLiquidityCount,
      highValueCount: stats.highValueCount,
      chainBreakdown: stats.chainBreakdown,
      topHoldings: stats.topHoldings,
    },
  };
}

function shortAddress(address) {
  const value = String(address || "").trim();
  if (value.length <= 10) {
    return value;
  }

  return `${value.slice(0, 6)}…${value.slice(-4)}`;
}

function isWebSocketSource(sourceUrl) {
  try {
    const parsed = new URL(sourceUrl);
    return parsed.protocol === "ws:" || parsed.protocol === "wss:";
  } catch (_) {
    return false;
  }
}

async function callRpcOverHttp(method, params = []) {
  const response = await fetch(SOURCE_URL, {
    method: "POST",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method,
      params,
    }),
  });

  if (!response.ok) {
    throw new Error(`RPC ${method} returned HTTP ${response.status}`);
  }

  const payload = await response.json();
  if (payload.error) {
    throw new Error(payload.error.message || `RPC ${method} failed`);
  }

  return payload.result;
}

async function callRpcOverWebSocket(method, params = []) {
  return new Promise((resolve, reject) => {
    const socket = new WebSocket(SOURCE_URL);
    const requestId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    let settled = false;
    let closeCode = null;
    let closeReason = "";

    const settle = (callback, value) => {
      if (settled) {
        return;
      }

      settled = true;
      try {
        socket.close();
      } catch (_) {
        // Ignore close errors; the promise already has a terminal state.
      }
      callback(value);
    };

    socket.addEventListener("open", () => {
      socket.send(JSON.stringify({
        jsonrpc: "2.0",
        id: requestId,
        method,
        params,
      }));
    });

    socket.addEventListener("message", (event) => {
      try {
        const rawMessage = typeof event.data === "string"
          ? event.data
          : Buffer.isBuffer(event.data)
            ? event.data.toString("utf8")
            : String(event.data);
        const payload = JSON.parse(rawMessage);
        if (payload.id !== requestId) {
          return;
        }

        if (payload.error) {
          settle(reject, new Error(payload.error.message || `RPC ${method} failed`));
          return;
        }

        settle(resolve, payload.result);
      } catch (error) {
        settle(reject, error);
      }
    });

    socket.addEventListener("error", () => {
      const suffix = closeCode !== null ? ` (close code ${closeCode}${closeReason ? `, reason: ${closeReason}` : ""})` : "";
      settle(reject, new Error(`RPC ${method} websocket connection failed${suffix}`));
    });

    socket.addEventListener("close", (event) => {
      closeCode = event.code;
      closeReason = event.reason || "";
      if (!settled) {
        settle(reject, new Error(`RPC ${method} websocket closed before a response was received (code ${event.code}${event.reason ? `, reason: ${event.reason}` : ""})`));
      }
    });
  });
}

async function callRpc(method, params = []) {
  if (isWebSocketSource(SOURCE_URL)) {
    return callRpcOverWebSocket(method, params);
  }

  return callRpcOverHttp(method, params);
}

async function loadRpcSnapshot() {
  const [chainIdHex, blockNumberHex, gasPriceHex, walletBalanceHex, walletNonceHex] = await Promise.all([
    callRpc("eth_chainId"),
    callRpc("eth_blockNumber"),
    callRpc("eth_gasPrice"),
    callRpc("eth_getBalance", [LIVE_WALLET_ADDRESS, "latest"]),
    callRpc("eth_getTransactionCount", [LIVE_WALLET_ADDRESS, "latest"]),
  ]);

  const blockNumber = hexToNumber(blockNumberHex);
  const chainId = hexToNumber(chainIdHex);
  const latestBlock = blockNumberHex ? await callRpc("eth_getBlockByNumber", [blockNumberHex, false]) : null;
  const blockTimestamp = latestBlock && latestBlock.timestamp ? hexToNumber(latestBlock.timestamp) : null;

  return {
    rpcMode: true,
    networkName: networkNameForChainId(chainId),
    chainId,
    blockNumber,
    blockHash: latestBlock && latestBlock.hash ? latestBlock.hash : null,
    blockTimestamp,
    blockTimestampIso: blockTimestamp ? new Date(blockTimestamp * 1000).toISOString() : null,
    gasPriceWei: gasPriceHex || null,
    gasPriceGwei: formatUnits(gasPriceHex, 9),
    walletAddress: LIVE_WALLET_ADDRESS || null,
    walletBalanceWei: walletBalanceHex || null,
    walletBalanceEth: formatUnits(walletBalanceHex, 18),
    walletNonce: hexToNumber(walletNonceHex),
    latestBlockTransactions: Array.isArray(latestBlock && latestBlock.transactions) ? latestBlock.transactions.length : null,
  };
}

async function loadLocalReport() {
  const raw = await fsp.readFile(REPORT_PATH, "utf8");
  return JSON.parse(raw);
}

async function loadUpstreamReport() {
  if (!SOURCE_URL) {
    return null;
  }
  const response = await fetch(SOURCE_URL, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Upstream source returned HTTP ${response.status}`);
  }
  return response.json();
}

async function loadReport() {
  if (isRpcSource(SOURCE_URL)) {
    try {
      const [localReport, liveChain] = await Promise.all([loadLocalReport(), loadRpcSnapshot()]);
      return normalizeReport(localReport, SOURCE_URL, {
        sourceType: "rpc",
        liveChain,
      });
    } catch (error) {
      const local = normalizeReport(await loadLocalReport(), REPORT_PATH, {
        sourceType: "local-file",
      });

      return {
        ...local,
        source: SOURCE_URL,
        sourceType: "rpc-fallback",
        upstreamError: error.message,
        liveChain: {
          rpcMode: true,
          networkName: "RPC unavailable",
          walletAddress: LIVE_WALLET_ADDRESS || null,
          error: error.message,
        },
      };
    }
  }

  if (SOURCE_URL) {
    try {
      const upstream = await loadUpstreamReport();
      if (upstream) {
        if (isDuneSnapshotPayload(upstream)) {
          return normalizeDuneReport(upstream, SOURCE_URL);
        }
        return normalizeReport(upstream, SOURCE_URL, {
          sourceType: "upstream-report",
        });
      }
    } catch (error) {
      const local = normalizeReport(await loadLocalReport(), REPORT_PATH, {
        sourceType: "local-file",
      });
      return {
        ...local,
        upstreamError: error.message,
      };
    }
  }

  return normalizeReport(await loadLocalReport(), REPORT_PATH, {
    sourceType: "local-file",
  });
}

function buildSignalsPayload(report) {
  return {
    generatedAt: report.generatedAt,
    source: report.source,
    sourceType: report.sourceType,
    summary: report.summary,
    preErrorFindings: report.preErrorFindings,
    withdrawSignals: report.withdrawSignals,
    placementSignals: report.placementSignals,
  };
}

function buildSummaryPayload(report) {
  return {
    generatedAt: report.generatedAt,
    source: report.source,
    sourceType: report.sourceType,
    sourceUrl: report.sourceUrl,
    liveChain: report.liveChain || null,
    duneSnapshot: report.duneSnapshot || null,
    summary: report.summary,
    preErrorCount: report.preErrorFindings.length,
    withdrawSignalFiles: report.withdrawSignals.length,
    placementSignalFiles: report.placementSignals.length,
  };
}

function buildStatusPayload(report) {
  const summary = buildSummaryPayload(report);
  const signals = buildSignalsPayload(report);
  const transactions = buildTransactionsPayload(report, LIVE_WALLET_ADDRESS);

  return {
    generatedAt: report.generatedAt,
    service: "financial-ops-rest-adapter",
    source: report.source,
    sourceType: report.sourceType,
    sourceUrl: report.sourceUrl,
    health: {
      ok: true,
      publicOrigin: PUBLIC_ORIGIN,
      reportSource: report.sourceType,
      liveChain: Boolean(report.liveChain),
      hasUpstreamError: Boolean(report.upstreamError),
    },
    summary,
    signals,
    transactions: {
      wallet: transactions.wallet,
      count: transactions.count,
      preview: transactions.transactions.slice(0, 5),
    },
    routes: [
      "/health",
      "/status",
      "/api/report",
      "/api/status",
      "/api/refresh",
      "/api/signals",
      "/api/summary",
      "/api/transactions",
      "/api/v1/member/:address",
    ],
    publicSurfaces: [
      "financial-ops-dashboard.html",
      "approval-service.html",
      "governance.html",
      "withdraw.html",
      "index.html",
    ],
    recommendedActions: report.recommendedActions,
  };
}

function buildTransactionsPayload(report, wallet) {
  const address = String(wallet || "").trim().toLowerCase();
  const transactions = [];

  if (report.liveChain) {
    const chain = report.liveChain;
    const blockNote = chain.sourceKind === "dune"
      ? `${chain.balanceCount || 0} balances across ${chain.chainCount || 0} chains`
      : chain.blockNumber !== null && chain.blockNumber !== undefined
        ? `Block ${chain.blockNumber}`
        : chain.error || "Live RPC snapshot";
    const amountLabel = chain.sourceKind === "dune"
      ? `${formatCurrency(chain.portfolioValueUsd) || "Unknown"} total`
      : chain.walletBalanceEth ? `${chain.walletBalanceEth} ETH` : "—";
    transactions.push({
      chain: chain.networkName || "Ethereum Mainnet",
      assetLabel: chain.sourceKind === "dune" ? "Portfolio snapshot" : "Live wallet snapshot",
      amountLabel,
      direction: "in",
      directionLabel: chain.sourceKind === "dune" ? "Snapshot" : "Live",
      recipientStatus: chain.walletAddress ? "match" : "unknown",
      recipientLabel: chain.walletAddress ? "Matches wallet" : "No wallet configured",
      transactionType: chain.sourceKind === "dune" ? "Dune snapshot" : "RPC snapshot",
      timestamp: chain.blockTimestampIso || report.generatedAt,
      from: report.source || "",
      to: chain.walletAddress || "",
      status: "confirmed",
      success: true,
      note: blockNote,
    });
  }

  if (report.duneSnapshot && (!report.liveChain || report.liveChain.sourceKind !== "dune")) {
    const snapshot = report.duneSnapshot;
    transactions.push({
      chain: "Dune",
      assetLabel: "Portfolio snapshot",
      amountLabel: `${formatCurrency(snapshot.totalValueUsd) || "Unknown"} total`,
      direction: "in",
      directionLabel: "Snapshot",
      recipientStatus: snapshot.walletAddress ? "match" : "unknown",
      recipientLabel: snapshot.walletAddress ? `Matches wallet` : "No wallet configured",
      transactionType: "Dune snapshot",
      timestamp: snapshot.responseTime || report.generatedAt,
      from: report.source || "",
      to: snapshot.walletAddress || "",
      status: "confirmed",
      success: true,
      note: `${snapshot.balanceCount || 0} balances across ${snapshot.chainCount || 0} chains`,
    });
  }

  for (const entry of report.successLog || []) {
    transactions.push({
      chain: "unknown",
      assetLabel: "Report event",
      amountLabel: "—",
      direction: "unknown",
      directionLabel: "Unclear",
      recipientStatus: "unknown",
      recipientLabel: address ? "Recipient unclear" : "No wallet supplied",
      transactionType: entry.title || "Report event",
      timestamp: entry.time || report.generatedAt,
      from: report.source || "",
      to: address || "",
      status: entry.status === "success" ? "confirmed" : "failed",
      success: entry.status === "success",
      note: entry.details || ""
    });
  }

  return {
    generatedAt: report.generatedAt,
    source: report.source,
    wallet: address || null,
    count: transactions.length,
    transactions,
  };
}

async function handleRequest(req, res) {
  const url = new URL(req.url, `http://${req.headers.host || `localhost:${PORT}`}`);

  if (req.method === "OPTIONS") {
    res.writeHead(204, {
      "Access-Control-Allow-Origin": PUBLIC_ORIGIN,
      "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Cache-Control": "no-store",
    });
    return res.end();
  }

  if (req.method === "GET" && url.pathname === "/") {
    const report = await loadReport();
    return html(
      res,
      200,
      `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Financial Ops REST Adapter</title>
  <style>
    body { margin: 0; font-family: Arial, sans-serif; background: #07111b; color: #e2e8f0; }
    main { max-width: 960px; margin: 0 auto; padding: 32px; }
    .panel { background: rgba(10, 25, 41, 0.9); border: 1px solid rgba(148, 163, 184, 0.18); border-radius: 18px; padding: 24px; }
    a { color: #7dd3fc; }
    code { background: rgba(15, 23, 42, 0.8); padding: 1px 6px; border-radius: 6px; }
  </style>
</head>
<body>
  <main>
    <section class="panel">
      <h1>Financial Ops REST Adapter</h1>
      <p>Serving report data for the dashboard from <code>${escapeHtml(report.source)}</code>.</p>
      <ul>
        <li><a href="/health">/health</a></li>
        <li><a href="/api/report">/api/report</a></li>
        <li><a href="/api/summary">/api/summary</a></li>
        <li><a href="/api/signals">/api/signals</a></li>
      </ul>
      <p>Source type: <strong>${escapeHtml(report.sourceType)}</strong></p>
      <p>Generated at: <strong>${escapeHtml(report.generatedAt)}</strong></p>
      <p>Dashboard link: <a href="http://127.0.0.1:8000/financial-ops-dashboard.html">Open dashboard</a></p>
    </section>
  </main>
</body>
</html>`
    );
  }

  if (req.method === "GET" && url.pathname === "/status") {
    const report = await loadReport();
    const status = buildStatusPayload(report);
    return html(
      res,
      200,
      `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DAO Status</title>
  <style>
    body { margin: 0; font-family: Arial, sans-serif; background: linear-gradient(180deg, #050816, #0f172a); color: #e2e8f0; }
    main { max-width: 1080px; margin: 0 auto; padding: 32px; }
    .hero { display: grid; gap: 16px; padding: 28px; border: 1px solid rgba(148,163,184,0.18); border-radius: 24px; background: rgba(15, 23, 42, 0.9); }
    .grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); margin-top: 20px; }
    .card { padding: 18px; border-radius: 18px; border: 1px solid rgba(148,163,184,0.18); background: rgba(2, 6, 23, 0.7); }
    h1, h2, h3, p { margin-top: 0; }
    ul { margin: 0; padding-left: 20px; }
    a { color: #7dd3fc; }
    code { background: rgba(15, 23, 42, 0.8); padding: 1px 6px; border-radius: 6px; }
    .muted { color: #94a3b8; }
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <p class="muted">Unified public control plane</p>
      <h1>DAO Status</h1>
      <p>Generated at <strong>${escapeHtml(status.generatedAt)}</strong> from <code>${escapeHtml(status.source)}</code>.</p>
      <p>Service health is <strong>${status.health.ok ? "ok" : "degraded"}</strong> and the current source type is <strong>${escapeHtml(status.sourceType)}</strong>.</p>
    </section>

    <section class="grid">
      <div class="card">
        <h2>Summary</h2>
        <p>Files scanned: <strong>${status.summary.summary.filesScanned}</strong></p>
        <p>Pre-errors: <strong>${status.summary.summary.preErrorCount}</strong></p>
        <p>Withdraw signals: <strong>${status.summary.summary.withdrawSignalCount}</strong></p>
        <p>Placement signals: <strong>${status.summary.summary.placementSignalCount}</strong></p>
      </div>

      <div class="card">
        <h2>Signals</h2>
        <p>Pre-error findings: <strong>${status.signals.preErrorFindings.length}</strong></p>
        <p>Withdrawal signals: <strong>${status.signals.withdrawSignals.length}</strong></p>
        <p>Placement signals: <strong>${status.signals.placementSignals.length}</strong></p>
      </div>

      <div class="card">
        <h2>Transactions</h2>
        <p>Wallet: <strong>${escapeHtml(status.transactions.wallet || "unspecified")}</strong></p>
        <p>Count: <strong>${status.transactions.count}</strong></p>
        <p>Preview entries: <strong>${status.transactions.preview.length}</strong></p>
      </div>

      <div class="card">
        <h2>Routes</h2>
        <ul>
          ${status.routes.map((route) => `<li><code>${escapeHtml(route)}</code></li>`).join("")}
        </ul>
      </div>
    </section>

    <section class="grid">
      <div class="card">
        <h2>Public Surfaces</h2>
        <ul>
          ${status.publicSurfaces.map((surface) => `<li>${escapeHtml(surface)}</li>`).join("")}
        </ul>
      </div>
      <div class="card">
        <h2>Recommended Actions</h2>
        <ul>
          ${status.recommendedActions.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
        </ul>
      </div>
    </section>

    <p class="muted">JSON API: <a href="/api/status">/api/status</a> · Report: <a href="/api/report">/api/report</a> · Summary: <a href="/api/summary">/api/summary</a></p>
  </main>
</body>
</html>`
    );
  }

  if (req.method === "GET" && url.pathname === "/health") {
    const report = await loadReport();
    return json(res, 200, {
      ok: true,
      service: "financial-ops-rest-adapter",
      port: PORT,
      source: report.source,
      sourceType: report.sourceType,
      generatedAt: report.generatedAt,
      duneSnapshot: report.duneSnapshot || null,
      upstreamError: report.upstreamError || null,
    });
  }

  if (req.method === "GET" && url.pathname === "/api/report") {
    const report = await loadReport();
    return json(res, 200, report);
  }

  if (req.method === "GET" && url.pathname === "/api/status") {
    const report = await loadReport();
    return json(res, 200, buildStatusPayload(report));
  }

  if (req.method === "POST" && url.pathname === "/api/refresh") {
    const report = await loadReport();
    return json(res, 200, {
      ok: true,
      refreshedAt: new Date().toISOString(),
      report,
    });
  }

  if (req.method === "GET" && url.pathname === "/api/signals") {
    builderFundUsage.record("/api/signals");
    const report = await loadReport();
    return json(res, 200, buildSignalsPayload(report));
  }

  if (req.method === "GET" && url.pathname === "/api/summary") {
    builderFundUsage.record("/api/summary");
    const report = await loadReport();
    return json(res, 200, buildSummaryPayload(report));
  }

  if (req.method === "GET" && url.pathname === "/api/transactions") {
    builderFundUsage.record("/api/transactions");
    const rawWallet = url.searchParams.get("wallet") || "";
    const wallet = sanitizeAddress(rawWallet);
    if (rawWallet && !wallet) {
      return json(res, 400, { error: "Invalid wallet address" });
    }
    const report = await loadReport();
    return json(res, 200, buildTransactionsPayload(report, wallet || ""));
  }

  // /api/v1/member/:address — personal member dashboard data
  const memberMatch = url.pathname.match(/^\/api\/v1\/member\/(0x[0-9a-fA-F]{40})$/i);
  if (req.method === "GET" && memberMatch) {
    const address = memberMatch[1].toLowerCase();
    builderFundUsage.record("/api/v1/member");
    const report = await loadReport();
    const transactions = buildTransactionsPayload(report, address);
    const chain = report.liveChain || null;
    return json(res, 200, {
      address,
      generatedAt: new Date().toISOString(),
      portfolio: {
        walletAddress: address,
        ethBalance: chain ? chain.walletBalanceEth : null,
        nonce: chain ? chain.walletNonce : null,
        networkName: chain ? chain.networkName : null,
        chainId: chain ? chain.chainId : null,
        blockNumber: chain ? chain.blockNumber : null,
        portfolioValueUsd: chain ? (chain.portfolioValueUsd || null) : null,
        topHoldings: chain ? (chain.topHoldings || []) : [],
      },
      governance: {
        note: "Query the NexusDAOGovernor contract on-chain for voting power and active proposals.",
      },
      treasury: {
        note: "Query the NexusDAOTreasury contract on-chain for real-time balances.",
      },
      transactions: {
        count: transactions.count,
        preview: transactions.transactions.slice(0, 10),
      },
      signals: buildSignalsPayload(report),
    });
  }

  // /api/v1/builder-fund/stats — read-only view of accumulated usage metrics
  // Used by the dashboard and by the Chainlink Automation upkeep to decide
  // when to submit a recordUsage() tx to NexusBuilderFund.sol.
  if (req.method === "GET" && url.pathname === "/api/v1/builder-fund/stats") {
    return json(res, 200, builderFundUsage.stats());
  }

  // /api/v1/builder-fund/usage — oracle relayer records off-chain usage
  // Expected body: { "endpoint": "/api/v1/member", "callCount": 42 }
  // Secured by the NEXUS_ORACLE_SECRET env var (Bearer token).
  if (req.method === "POST" && url.pathname === "/api/v1/builder-fund/usage") {
    const authHeader = req.headers.authorization || "";
    const oracleSecret = String(process.env.NEXUS_ORACLE_SECRET || "").trim();
    if (oracleSecret && authHeader !== "Bearer " + oracleSecret) {
      return json(res, 401, { error: "Unauthorized" });
    }
    let body = "";
    for await (const chunk of req) body += chunk;
    let parsed;
    try { parsed = JSON.parse(body); } catch (_) {
      return json(res, 400, { error: "Invalid JSON body" });
    }
    const endpoint = String(parsed.endpoint || "").trim();
    const callCount = Math.floor(Number(parsed.callCount));
    if (!endpoint) return json(res, 400, { error: "endpoint required" });
    if (!Number.isFinite(callCount) || callCount < 1) {
      return json(res, 400, { error: "callCount must be a positive integer" });
    }
    builderFundUsage.record(endpoint, callCount);
    return json(res, 200, {
      ok: true,
      endpoint,
      callCount,
      stats: builderFundUsage.stats(),
    });
  }

  return json(res, 404, {
    error: "Not found",
    routes: [
      "/", "/status", "/health",
      "/api/report", "/api/status", "/api/refresh",
      "/api/signals", "/api/summary", "/api/transactions",
      "/api/v1/member/:address",
      "/api/v1/builder-fund/stats",
      "/api/v1/builder-fund/usage",
    ],
  });
}

function isValidEthAddress(value) {
  return /^0x[0-9a-fA-F]{40}$/.test(String(value || "").trim());
}

function sanitizeAddress(value) {
  const trimmed = String(value || "").trim();
  if (!trimmed) return null;
  if (!isValidEthAddress(trimmed)) return null;
  return trimmed.toLowerCase();
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

async function bootstrap() {
  const server = http.createServer((req, res) => {
    handleRequest(req, res).catch((error) => {
      json(res, 500, {
        error: error.message || "Internal server error",
      });
    });
  });

  server.listen(PORT, "0.0.0.0", () => {
    console.log(`Financial ops REST adapter listening on http://localhost:${PORT}`);
  });
}

bootstrap().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
