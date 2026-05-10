# Financial Ops Live Adapter Spec

This document defines the live data contract for the financial ops dashboard and REST adapter. It turns the strategy-oriented crypto guide into a concrete payload shape that can be served from an upstream API, RPC-backed indexer, or local file fallback.

## Purpose

The dashboard should consume one normalized report object and a small set of derived endpoints. The upstream source may be any of the following:

- a JSON report service
- an RPC-backed indexer
- a chain analytics job that exports JSON
- a local file used as fallback in development

The adapter's job is to normalize whichever source is available into the same response shape.

## Canonical Report Shape

The upstream report should provide these top-level fields:

```json
{
  "generatedAt": "2026-04-14T12:00:00Z",
  "summary": {
    "filesScanned": 0,
    "preErrorCount": 0,
    "withdrawSignalCount": 0,
    "placementSignalCount": 0,
    "approvalGate": "required for any fund movement or treasury action"
  },
  "bots": [],
  "preErrorFindings": [],
  "withdrawSignals": [],
  "placementSignals": [],
  "successLog": [],
  "recommendedActions": [],
  "liveChain": null,
  "duneSnapshot": null,
  "balances": []
}
```

## Field Definitions

### generatedAt

- Type: string
- Format: ISO 8601 timestamp
- Required: yes

Timestamp used for freshness checks and auto-refresh behavior.

### summary

Required object with these fields:

- `filesScanned`: number
- `preErrorCount`: number
- `withdrawSignalCount`: number
- `placementSignalCount`: number
- `approvalGate`: string

### bots

Array of bot descriptors:

```json
{
  "id": "mcp-fin-011",
  "name": "Pre-Error Remediation Bot",
  "role": "Detect early failures and malformed configs."
}
```

Required fields:

- `id`: string
- `name`: string
- `role`: string

### preErrorFindings

Array of findings with:

- `severity`: string, expected values `low`, `medium`, `high`, or `success`
- `category`: string
- `file`: string
- `message`: string

### withdrawSignals

Array of withdrawal-related signals with:

- `file`: string
- `count`: number
- `matches`: array of strings

### placementSignals

Array of placement/revenue-related signals with the same shape as `withdrawSignals`.

### successLog

Array of operational success events with:

- `time`: string, ISO 8601 timestamp recommended
- `title`: string
- `details`: string
- `status`: string, usually `success` or `failed`

### recommendedActions

Array of operator-facing next steps as strings.

### liveChain

Optional object attached when the source is a live RPC endpoint rather than a static report feed. Suggested fields:

- `rpcMode`: boolean
- `networkName`: string
- `chainId`: number
- `blockNumber`: number
- `blockHash`: string
- `blockTimestamp`: number
- `blockTimestampIso`: string
- `gasPriceWei`: string
- `gasPriceGwei`: string
- `walletAddress`: string
- `walletBalanceWei`: string
- `walletBalanceEth`: string
- `walletNonce`: number
- `latestBlockTransactions`: number

### duneSnapshot

Optional object attached when the source is a Dune-style holdings export rather than an RPC snapshot. Suggested fields:

- `walletAddress`: string
- `requestTime`: string
- `responseTime`: string
- `nextOffset`: string
- `balanceCount`: number
- `chainCount`: number
- `totalValueUsd`: number
- `nativeValueUsd`: number
- `lowLiquidityCount`: number
- `highValueCount`: number
- `chainBreakdown`: object keyed by chain name
- `topHoldings`: array of the largest holdings by USD value

### balances

Normalized holdings array for Dune-style payloads. Each item should include:

- `chain`: string
- `chainId`: number
- `address`: string
- `amount`: string
- `amountDisplay`: string
- `symbol`: string
- `name`: string
- `decimals`: number
- `priceUsd`: number
- `valueUsd`: number
- `valueUsdLabel`: string
- `poolSize`: number
- `lowLiquidity`: boolean
- `isNative`: boolean

## Adapter Endpoints

The REST adapter should expose these routes:

- `GET /health`
- `GET /api/report`
- `POST /api/refresh`
- `GET /api/signals`
- `GET /api/summary`
- `GET /api/transactions?wallet=<address>`

## Endpoint Contracts

### GET /api/report

Returns the fully normalized report object.

### GET /api/signals

Returns a compact payload for the signal panels:

- `generatedAt`
- `source`
- `sourceType`
- `summary`
- `preErrorFindings`
- `withdrawSignals`
- `placementSignals`

### GET /api/summary

Returns a summary-only payload:

- `generatedAt`
- `source`
- `sourceType`
- `sourceUrl`
- `summary`
- `preErrorCount`
- `withdrawSignalFiles`
- `placementSignalFiles`

### GET /api/transactions?wallet=<address>

Returns a transaction-style projection derived from report events or upstream chain activity.

Required response fields:

- `generatedAt`
- `source`
- `wallet`
- `count`
- `transactions`

Each transaction should include:

- `chain`
- `assetLabel`
- `amountLabel`
- `direction`
- `directionLabel`
- `recipientStatus`
- `recipientLabel`
- `transactionType`
- `timestamp`
- `from`
- `to`
- `status`
- `success`
- `note`

## Normalization Rules

The adapter should normalize source data as follows:

- Convert missing counts to `0`.
- Convert missing arrays to empty arrays.
- Preserve upstream timestamps when present.
- Add `sourceType` so the dashboard can distinguish `upstream` from `local-file`.
- Attach `liveChain` when the source is a JSON-RPC endpoint.
- Attach `duneSnapshot` and `balances` when the source is a Dune-style holdings export.
- Preserve upstream errors in `upstreamError` when the live source fails and the fallback is used.
- Ensure all payloads remain valid JSON without requiring the browser to interpret raw RPC structures.

## Live Source Options

Recommended upstream source types:

1. JSON report endpoint produced by a scheduled job.
2. Chain indexer service that exports the canonical report object.
3. RPC-backed adapter that aggregates wallet activity and emits the canonical report shape.

If the upstream source is raw chain data, the adapter should be responsible for converting it into the canonical report and transaction projection rather than exposing raw RPC responses directly to the dashboard.

Suggested environment variables for RPC mode:

- `FINANCIAL_OPS_SOURCE_URL`: the JSON-RPC endpoint
- `FINANCIAL_OPS_SOURCE_KIND=rpc`: force RPC mode when auto-detection is not enough
- `FINANCIAL_OPS_WALLET_ADDRESS`: the wallet to snapshot

## Development Fallback

If no live source is configured, the adapter may fall back to `ops/reports/financial-ops-report.json` so the dashboard remains usable offline.
