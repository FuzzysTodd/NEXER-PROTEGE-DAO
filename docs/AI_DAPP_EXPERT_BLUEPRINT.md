# Nexus AI Dapp Expert Blueprint

## Goal
Build an expert AI operator for the Nexus dapp that can reason across governance, treasury, signal reliability, routing rails, token metadata, and source trust.

## Core Capabilities
- Source-of-truth reasoning from canonical repository and governed manifest entries.
- Execution guidance for send, withdrawal, settlement, and route preflight.
- Signal health analysis from WebSocket and REST probes.
- Governance-aware recommendations aligned to owner authority and approval boundaries.
- Redundancy-aware incident guidance for runtime failover and data drift.

## Data Inputs
- `dao-data-source-manifest.json`
- dapp runtime telemetry (signal feed, endpoint latency, route status)
- token credential profiles (per-chain metadata)
- governance policy docs and owner authority references
- ops reports and approved external sources

## Safety and Governance Rules
- Never request or store private keys, mnemonics, or secrets.
- Flag low-trust sources and recommend verification before execution.
- Require explicit approval for irreversible actions.
- Keep decisions auditable with source references and confidence.

## Operator Modes
- Guided mode: ordered, approval-aware execution.
- Open mode: expert exploration with policy overlays.

## Build Plan
1. Add AI context assembler from manifest + runtime panels.
2. Add rail-route recommendation engine with confidence scoring.
3. Add governance policy checker before action execution.
4. Add explainability panel: why a recommendation was made.
5. Add incident runbook generation from active telemetry.
