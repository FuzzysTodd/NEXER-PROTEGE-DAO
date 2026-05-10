---
applyTo: "contracts/**/*.sol"
---

## Solidity Smart Contract Guidelines

When writing or modifying Solidity smart contracts in this repository, follow these conventions:

1. **Compiler version** — always use `pragma solidity ^0.8.20;`.
2. **OpenZeppelin** — import from `@openzeppelin/contracts` for ERC standards, access control, and security primitives. Do not reimplement functionality already provided by OpenZeppelin.
3. **Reentrancy protection** — apply `ReentrancyGuard` and the `nonReentrant` modifier to any function that transfers ETH or tokens.
4. **Access control** — use `Ownable` or `AccessControl` from OpenZeppelin. Avoid `tx.origin` for authentication.
5. **SafeERC20** — use `SafeERC20` for all ERC-20 token transfers.
6. **ETH transfers** — prefer `(bool success, ) = recipient.call{value: amount}("");` over `.transfer()` or `.send()`.
7. **Events** — emit a descriptive event for every state-changing operation.
8. **NatSpec** — document all `public` and `external` functions with `/// @notice`, `/// @param`, and `/// @return` tags.
9. **Nexus Encryption Standard (NES)** — follow conventions in `docs/NEXUS_ENCRYPTION_STANDARD.md` for any signing or message-protection logic.
10. **Testing** — every new function that handles funds or alters critical state must have a corresponding Hardhat unit test.
11. **Linting** — run `npx solhint 'contracts/**/*.sol'` before committing.
12. **No secrets** — never hard-code private keys, seeds, or sensitive addresses directly in contract source.
