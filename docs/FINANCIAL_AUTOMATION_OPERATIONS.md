# Financial Automation Operations

This repository now includes a finance-operations automation layer built around three additional bots:

- Pre-Error Remediation Bot
- Withdrawal Placement Scanner
- Success Documentation Reporter

## Purpose

The automation layer is designed to reduce operational drag across repository maintenance, financial-flow review, and reporting. It does not autonomously move funds. Any withdrawal execution, treasury reallocation, or settlement-impacting change remains human-gated.

## Bot Responsibilities

### Pre-Error Remediation Bot

- Checks repository-owned Python files for syntax failures.
- Checks JSON configuration files for parse errors.
- Checks custom agent files for missing frontmatter.
- Flags suspicious repository-owned filenames that make automation or reporting brittle.

### Withdrawal Placement Scanner

- Scans the repo for withdrawal, claim, release, redeem, and payout paths.
- Surfaces capital-allocation signals such as treasury, liquidity, staking, APY, rebalance, and revenue distribution logic.
- Produces ranked recommendations instead of executing treasury actions.

### Success Documentation Reporter

- Writes markdown and JSON summaries on every successful scan.
- Keeps dashboard data aligned with generated operator documentation.
- Preserves a simple success journal that can be rendered in a browser interface.

## Files Added

- `.github/agents/preerror-remediation-bot.agent.md`
- `.github/agents/withdrawal-placement-scanner.agent.md`
- `.github/agents/success-documentation-reporter.agent.md`
- `mcp/agents/financial-ops-bots.json`
- `nexus/finance_ops_report.py`
- `.github/workflows/financial-ops-automation.yml`
- `ops/reports/financial-ops-report.json`
- `ops/reports/financial-ops-report.md`
- `financial-ops-dashboard.html`

## Automation Flow

1. GitHub Actions runs the financial ops workflow on demand, on schedule, and on relevant pushes.
2. `nexus/finance_ops_report.py` scans the repository and generates JSON plus markdown reports.
3. The markdown report is published into the workflow job summary and uploaded as an artifact.
4. The JSON report is consumed by the web dashboard or by other tooling.

## Approval Boundary

The automation layer can detect issues, suggest fixes, and produce reports. It must not:

- submit transactions
- withdraw treasury funds
- rotate signers
- rebalance assets
- alter payout logic without human review

## Automation Authority

Repository automation is authorized to:

- scan the repository continuously
- generate and refresh reports and dashboard payloads
- prepare and apply low-risk code and configuration fixes
- create documentation and operator-facing summaries
- perform repository code changes and local git preparation work

Repository automation is not authorized to:

- move funds automatically
- approve treasury actions by itself
- submit irreversible on-chain actions without a human decision
- treat yield or placement suggestions as guaranteed returns

This keeps coding and reporting automation broad while preserving a hard approval boundary for financial execution.

## Recommended Operating Pattern

1. Run the workflow.
2. Review `ops/reports/financial-ops-report.md`.
3. Open `financial-ops-dashboard.html` for a summarized operator view.
4. Use the custom bots for targeted remediation or documentation updates.
