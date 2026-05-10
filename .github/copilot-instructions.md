---
applyTo: "**/*"
---

## Copilot Instructions for This Repository

Follow these rules when implementing changes:

1. Make minimal, targeted edits only. Do not rewrite unrelated files.
2. Do not modify third-party protocol reference directories (`Aave-V3/`, `Uniswap-V3/`, `Olympus-DAO/`, etc.) unless explicitly requested.
3. Never add secrets (private keys, mnemonics, tokens, or sensitive addresses) to source files.
4. Treat `@FuzzysTodd` as the owner and final authority for governance, deployment, and irreversible actions.
5. Use `README.md`, `GOVERNANCE.md`, and `docs/` as the project source of truth for architecture and process.
6. Prefer safe, reversible automation changes unless the task explicitly requires otherwise.
7. If anything is ambiguous or blocked, stop and report the blocker instead of guessing.

## Validation

- Python/tooling setup: `python -m pip install -r requirements-dev.txt`
- Main test command: `pytest -q`
- Optional lint command used in this repo: `flake8 .` (this can report pre-existing issues unrelated to your change)

## Language-Specific Guidance

- Python: use the configured conda environment when available.
- Frontend (`.html`, `.js`): keep pages framework-free and self-contained; use `ethers.js` only where existing Web3 behavior already uses it.
- Solidity (`contracts/**/*.sol`): follow `instructions/solidity.instructions.md`.

### MCP & Workflow Operations

- For workflow, CI, and MCP orchestration tasks, prioritize repository expert agents:
  - `preerror-remediation-bot` for workflow failures and config drift
  - `financial-rails-signal` for transaction and settlement signal workflows
  - `success-documentation-reporter` for runbooks and operational reporting
- Keep workflow permissions least-privilege and avoid broad write scopes unless explicitly required.
