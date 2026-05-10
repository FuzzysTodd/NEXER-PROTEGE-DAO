---
applyTo: "**/*"
---

## Repository Instructions

When working in this repository:

1. Prefer minimal, targeted changes. Do not rewrite unrelated code or docs.
2. Never modify third-party reference directories unless explicitly instructed.
3. Never commit secrets, private keys, mnemonics, or sensitive addresses.
4. Treat `@FuzzysTodd` as the owner and primary authority for governance, deployment, and irreversible actions.
5. Use the existing repo structure and conventions in `GOVERNANCE.md`, `README.md`, and `docs/` as the source of truth.
6. Keep automation safe: use read-only or reversible changes unless the task explicitly requires something else.
7. Validate changes with the relevant tests or checks before handing them back.
8. If an operation is blocked or ambiguous, stop and report the blocker instead of guessing.

### Python

- Use the configured conda environment when running Python code.
- Prefer `requirements-dev.txt` for tests and tooling.
- Run `pytest` for Python validation when applicable.

### Frontend

- Keep HTML/JS pages self-contained and free of framework dependencies.
- Use `ethers.js` for Web3 interactions only when the file already uses Web3 behavior.

### Solidity

- Follow the repository Solidity guidance in [solidity.instructions.md](solidity.instructions.md).
