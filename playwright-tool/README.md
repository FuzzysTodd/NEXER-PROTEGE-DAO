# 💰 Nexus Protocol Web3 Automation Tool

**Simplified Playwright automation for Nexus Protocol contract interactions**

Reduce manual steps. Maximize token earnings. Automate withdrawals, transfers, and contract interactions with minimal effort.

---

## 🎯 What This Tool Does

This downloadable Playwright tool helps you:

- ✅ **Automate Wallet Connection** - One-click MetaMask connection
- ✅ **Withdraw from Contracts** - Automated withdrawal workflows
- ✅ **Transfer Tokens** - Easy token transfer automation
- ✅ **Interact with Nexus Contracts** - Seamless contract interactions
- ✅ **Maximize Earnings** - Efficient multi-contract management

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install

```bash
cd playwright-tool
./install.sh
```

### Step 2: Start Server (in another terminal)

```bash
cd ..
python3 -m http.server 3000
```

### Step 3: Run Automation

```bash
npm run web3-automate
```

**That's it!** The tool will:
1. Open your browser
2. Guide you to connect MetaMask  
3. Show you all your contracts
4. Highlight withdraw buttons
5. Let you execute transactions with minimal clicks

---

## 📋 Available Commands

| Command | Description |
|---------|-------------|
| `npm run web3-automate` | **Main tool** - Automate wallet connection, withdrawals, transfers |
| `npm run quick-start` | Quick demo - takes screenshots of pages |
| `npm test` | Run full test suite |
| `npm run test-headed` | Run tests with visible browser |
| `npm run codegen` | Record your own automation scripts |

---

## 💡 How to Use for Maximum Earnings

### Withdrawing from Multiple Contracts

1. Run the automation:
   ```bash
   npm run web3-automate
   ```

2. The tool will:
   - ✅ Highlight the "Connect Wallet" button in green
   - ✅ Wait for you to approve MetaMask
   - ✅ Show all your contracts
   - ✅ Highlight all "Withdraw" buttons

3. Simply click each highlighted "Withdraw" button and approve in MetaMask

4. The browser stays open for 5 minutes, allowing you to process multiple withdrawals

### Adding New Contracts

The automation will:
- Detect if you have no contracts
- Highlight the "Add Contract" form
- Wait for you to fill it in
- Continue once the contract is added

---

## 🛠️ Advanced Usage

### Create Your Own Automation

Use Playwright's codegen to record your own workflows:

```bash
npm run codegen http://localhost:3000/withdraw.html
```

This will:
- Open a browser
- Record your actions
- Generate code you can save and reuse

### Run Tests Automatically

```bash
npm test  # Runs all tests
npm run test-headed  # See tests run in browser
```

---

## 📦 What's Included

```
playwright-tool/
├── install.sh              # One-click installer
├── package.json            # Dependencies
├── playwright.config.js    # Pre-configured settings
├── scripts/
│   ├── web3-automation.js  # Main Web3 automation
│   ├── quick-start.js      # Quick demo
│   └── automate.js         # Full automation suite
├── tests/
│   └── example.spec.js     # Example tests
└── README.md              # This file
```

---

## 🔧 Configuration

### Change Base URL

Edit `playwright.config.js`:

```javascript
baseURL: 'http://localhost:3000',  // Change port here
```

### Adjust Timing

Edit `scripts/web3-automation.js`:

```javascript
slowMo: 1000,      // Milliseconds between actions
timeout: 300000    // How long to wait (5 min = 300000ms)
```

---

## ❓ Troubleshooting

### MetaMask Not Detected

- Install MetaMask browser extension
- Refresh the page
- Make sure you're using Chrome/Chromium

### Connection Issues

```bash
# Make sure server is running:
cd .. && python3 -m http.server 3000

# In another terminal, run automation:
cd playwright-tool
npm run web3-automate
```

### Browser Closes Too Fast

Edit `web3-automation.js` and increase timeout:

```javascript
await page.waitForTimeout(300000); // 5 minutes
// Change to:
await page.waitForTimeout(600000); // 10 minutes
```

---

## 📸 Screenshots

All screenshots are saved to `screenshots/` directory:

- `step1-loaded.png` - Initial page load
- `step2-connect-highlighted.png` - Connect button highlighted
- `step2-connected.png` - Wallet connected
- `step4-add-contract-form.png` - Add contract form (if needed)
- `step5-contracts-ready.png` - All contracts ready for withdrawal

---

## 🎓 Tips for Maximum Efficiency

1. **Keep the automation running** - It will wait while you approve transactions
2. **Use the highlights** - Green borders show what to click
3. **Check screenshots** - If something goes wrong, check the saved screenshots
4. **Batch operations** - Add all your contracts first, then withdraw from all at once
5. **Rerun anytime** - The automation is idempotent - safe to run multiple times

---

## 🔐 Security

- ✅ All code is open source and auditable
- ✅ Never stores your private keys
- ✅ You approve every transaction in MetaMask
- ✅ Runs locally on your machine
- ✅ No data sent to external servers
- 🔒 MCP server stays sandboxed by default—keep `PLAYWRIGHT_MCP_ALLOW_UNRESTRICTED_FILE_ACCESS` **unset/0**. Only enable it intentionally if you need global `file://` access and fully trust the environment.

---

## 📄 License

MIT License - Free to use, modify, and distribute

---

## 🤝 Support

Having issues? Check:
1. Screenshots in `screenshots/` directory
2. Error messages in terminal
3. Make sure server is running on correct port

---

## 🎉 Happy Automating!

This tool is designed to **reduce manual steps and maximize your earnings** by making contract interactions as simple as possible.

**One command to rule them all:**
```bash
npm run web3-automate
```
