---
ready_for_review: true
---

## Summary
<!-- One paragraph: what does this PR do and why? -->


## Type of Change
<!-- Check all that apply -->
- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 🔒 Security improvement
- [ ] ⚙️  Refactor / cleanup (no functional change)
- [ ] 📚 Documentation update
- [ ] 🔧 CI/CD / automation change
- [ ] 💎 New Solidity contract or contract upgrade
- [ ] 🌐 Frontend / dashboard change

## Files Changed
<!-- List the key files modified and why -->


## Testing
<!-- How was this tested? -->
- [ ] `python -m pytest -q` passes (all tests green)
- [ ] `python -m flake8 .` passes (no lint errors)
- [ ] JavaScript files pass `node --check`
- [ ] HTML pages load correctly in browser
- [ ] New Solidity contracts pass `solhint`

## Security Checklist
- [ ] No secrets, private keys, or mnemonics added to any file
- [ ] Reentrancy guards applied to all fund-movement functions
- [ ] Access control roles verified (EXECUTOR_ROLE, GUARDIAN_ROLE)
- [ ] Multi-sig threshold respected for large treasury transfers
- [ ] Input validation added for all user-supplied values

## Governance Alignment
- [ ] Changes comply with `GOVERNANCE.md`
- [ ] Owner (`@FuzzysTodd`) approval obtained (or this is a Copilot-agent PR awaiting review)
- [ ] Timelock delay requirements respected for on-chain changes

## Related Issues / References
<!-- Link any related issues: "Closes #123" or "Refs #456" -->


## Deployment Notes
<!-- Any deployment steps, contract addresses to update, env vars needed? -->

