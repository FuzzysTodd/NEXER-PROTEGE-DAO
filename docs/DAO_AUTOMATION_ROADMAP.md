# DAO Automation Roadmap

This document summarizes the repository surfaces that already support automation, then identifies the missing pieces needed to make the DAO more public-facing and more self-operating.

## Existing Automation Surfaces

- [Financial automation operations](FINANCIAL_AUTOMATION_OPERATIONS.md) already defines repo-scanning bots for pre-error remediation, withdrawal placement review, and success reporting.
- [Automation authority](AUTOMATION_AUTHORITY.md) already authorizes repository scans, documentation updates, report generation, and low-risk repository changes while keeping treasury execution human-gated.
- [Financial ops REST adapter](financial-ops-live-adapter-spec.md) already defines a public data contract and routes for report, summary, signal, and transaction projections.
- [Approval service server](../approval-service-server.js) already exposes REST endpoints for health, service URL management, service testing, and audit exports.
- [Financial ops REST server](../financial-ops-rest-server.js) already serves `/health`, `/status`, `/api/report`, `/api/status`, `/api/refresh`, `/api/signals`, `/api/summary`, and `/api/transactions`.
- GitHub Pages now provides free static hosting for the public surfaces and the latest report snapshots via `.github/workflows/public-pages.yml`.
- GitHub Actions workflows already schedule report generation and orchestration through `.github/workflows/financial-ops-automation.yml`, `.github/workflows/mcp-gateway-orchestrator.yml`, `.github/workflows/progress-report-email.yml`, and `.github/workflows/main.yml`.
- The public website already has operator-facing surfaces in `index.html`, `financial-ops-dashboard.html`, `approval-service.html`, `withdraw.html`, and `governance.html`.

## What Can Be Automated Now

### 1. Public reporting

- Publish generated reports on a schedule.
- Refresh dashboard payloads automatically from local JSON, upstream report services, or chain/RPC sources.
- Push summaries into GitHub job summaries, artifacts, and dashboard pages.
- Use free static hosting for the current public site and report snapshots instead of paid storage.

### 2. Service health and audit

- Expose health endpoints for each operational service.
- Keep audit logs for service URL changes, test runs, report refreshes, and workflow outcomes.
- A unified status view is now available in the financial ops REST adapter and can be expanded to include other services.

### 3. Routine ops automation

- Scan for pre-errors, broken configs, and risky filenames.
- Detect withdrawal, payout, or placement signals and rank them for review.
- Generate markdown and JSON reports for humans and downstream tools.

### 4. Public control-plane behavior

- Serve canonical read-only DAO data over stable REST endpoints.
- Allow dashboards and external tools to consume one normalized report shape.
- Provide a transaction-style projection for activity summaries without exposing raw RPC structures.

## What Should Stay Human-Gated

- Treasury movements.
- Withdrawal execution.
- Signer rotation.
- Contract upgrades.
- Token minting or burning.
- Any irreversible on-chain or financial action.

Automation can prepare, recommend, and stage these operations, but it should not execute them autonomously.

## Missing Pieces For A Self-Operating DAO

### 1. Unified API gateway

The financial ops REST adapter now exposes a unified status route. The next step is to grow that into a fuller public-facing service that aggregates the existing REST endpoints into a consistent DAO control plane. It should expose:

- `/health`
- `/status`
- `/governance`
- `/reports`
- `/signals`
- `/treasury-summary`
- `/actions`
- `/transactions`

### 2. OpenAPI or route manifest

Document the REST surface in a machine-readable form so bots, dashboards, and downstream services can discover the API without reading source code.

### 3. Webhook/event ingestion

Add a small event layer that accepts trusted callbacks from:

- GitHub Actions
- chain indexers
- wallet or treasury monitors
- off-chain analytics jobs

### 4. Scheduled publication pipeline

Add workflow steps that:

- regenerate reports,
- publish static artifacts,
- update dashboards,
- and notify operators when a meaningful state change occurs.

### 5. Role-based approval flow

Keep read-only and reporting endpoints public, but isolate approval, treasury, and execution endpoints behind explicit permissions and signed authorization.

### 6. Observability

Add structured logs, timestamps, and reproducible state snapshots so the DAO can explain why a report, alert, or recommendation was produced.

## Recommended Implementation Order

1. Unify the current REST services behind one public DAO status API.
2. Add OpenAPI or route documentation for every exposed endpoint.
3. Connect GitHub Actions to refresh reports and publish summaries on a schedule.
4. Add webhook intake for report updates and external chain signals.
5. Keep approval-gated paths separate from public read-only paths.
6. Extend dashboards to consume the unified status API instead of ad hoc files.

## Practical Outcome

If implemented in that order, the DAO becomes:

- publicly readable through stable APIs,
- continuously reportable through scheduled workflows,
- auditable through exported logs and summaries,
- and self-operating for low-risk maintenance while preserving human control over money and irreversible actions.
