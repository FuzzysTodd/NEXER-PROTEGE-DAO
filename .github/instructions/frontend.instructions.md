---
applyTo: "**/*.{html,js}"
---

## Frontend (HTML/JavaScript) Guidelines

When writing or modifying frontend pages and scripts in this repository:

1. **No framework** — use plain ES6+ JavaScript. Do not introduce React, Vue, or any bundler unless explicitly asked.
2. **Web3 library** — use `ethers.js` (loaded from CDN) for all blockchain interactions. Keep the CDN version consistent with what is already used in the file being modified.
3. **Self-contained pages** — each `.html` page should work standalone. Shared logic may be placed in a co-located `.js` file (e.g., `logical.js`, `money-flow.js`).
4. **No secrets** — never embed private keys, mnemonics, or API secrets in HTML or JS files.
5. **Input validation** — validate all user-supplied values (addresses, amounts) before passing them to contract calls.
6. **Error handling** — wrap all `async` Web3 calls in `try/catch` and surface human-readable error messages to the user.
7. **MetaMask / wallet** — use `window.ethereum` for wallet connections; check for its presence before calling it.
8. **Accessibility** — include `alt` attributes on images and meaningful `aria-label` attributes on interactive elements.
9. **Style** — follow the existing CSS conventions in the file; do not introduce external CSS frameworks unless the file already uses one.
10. **Third-party reference directories** — do not modify HTML/JS files inside protocol reference directories (`Aave-V3/`, `Uniswap-V3/`, etc.).
