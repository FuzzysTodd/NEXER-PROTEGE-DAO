# ⚡ Quick Start Guide - Nexus Playwright Tool

## For Maximum Token Earnings with Minimal Effort

---

## 🎯 What This Tool Does

**Automates your Web3 workflow** so you can:
- Withdraw from contracts with 2 clicks instead of 20
- Transfer tokens automatically  
- Interact with multiple Nexus contracts efficiently
- Maximize earnings by reducing time spent on manual tasks

---

## 🚀 Get Started in 60 Seconds

### 1️⃣ Install (30 seconds)

```bash
cd playwright-tool
./install.sh
```

Output will look like:
```
💰 Nexus Protocol Web3 Automation Tool
======================================

✓ Node.js found: v18.x.x
📦 Installing dependencies...
🌐 Installing Chromium browser...
✅ Installation complete!
```

### 2️⃣ Start Server (10 seconds)

Open a new terminal and run:
```bash
cd ..
python3 -m http.server 3000
```

### 3️⃣ Run Automation (20 seconds to start)

In your original terminal:
```bash
npm run web3-automate
```

---

## 💰 Your First Withdrawal

When the automation runs, you'll see:

```
💰 Nexus Protocol Web3 Automation
==================================

This tool automates:
  ✓ Wallet connection
  ✓ Contract withdrawals
  ✓ Token transfers
  ✓ Contract interactions

🔗 Step 1: Opening Withdraw Manager...
  ✓ Withdraw Manager loaded

🔌 Step 2: Connecting Wallet...
  ⚠️  ACTION REQUIRED: Click "Connect Wallet" when ready
  💡 Connect button highlighted in green
```

**What happens:**
1. Browser opens showing withdraw manager
2. "Connect Wallet" button **glows green** ← Click this
3. MetaMask popup appears → Approve it
4. Your contracts load automatically
5. All "Withdraw" buttons **glow green** ← Click any/all
6. Approve transactions in MetaMask
7. Done! 💰

---

## 🎮 Interactive Guide

### Step 1: Connect Wallet
- Green glow = what to click
- MetaMask will pop up
- Click "Connect"

### Step 2: Add Contracts (if needed)
- If no contracts, form appears
- Highlighted in green
- Fill in: address, method
- Click "Add Contract"

### Step 3: Withdraw
- Each contract card has green border
- Click any "Withdraw" button
- Approve in MetaMask
- Wait for confirmation

### Step 4: Repeat
- Browser stays open 5 minutes
- Withdraw from multiple contracts
- All in one session

---

## 📸 Screenshots

Check `screenshots/` folder after running:
- See exactly what happened
- Verify transactions
- Troubleshoot if needed

---

## 🔧 Customization

### Change Wait Time

Edit `scripts/web3-automation.js`:
```javascript
// Line 98:
await page.waitForTimeout(300000); // 5 min

// Change to:
await page.waitForTimeout(600000); // 10 min
```

### Change Server Port

Edit `playwright.config.js`:
```javascript
baseURL: 'http://localhost:3000',  // Change 3000 to your port
```

---

## ❓ Troubleshooting

### "MetaMask not installed"
→ Install MetaMask browser extension

### "Connection refused"
→ Make sure server is running: `python3 -m http.server 3000`

### "Button not found"
→ Check screenshots/ folder to see what's wrong

### Browser closes too fast
→ Increase timeout in `web3-automation.js` (see Customization)

---

## 🎓 Pro Tips

1. **Run before withdrawing** - Let automation set everything up
2. **Keep terminal open** - See progress messages
3. **Check screenshots** - Visual record of everything
4. **Batch operations** - Add all contracts first, then withdraw
5. **Rerun anytime** - Safe to run multiple times

---

## 📊 Example Session

```bash
Terminal 1:
$ cd playwright-tool
$ ./install.sh
✅ Installation complete!

$ npm run web3-automate
💰 Nexus Protocol Web3 Automation
🔗 Step 1: Opening Withdraw Manager...
  ✓ Withdraw Manager loaded
🔌 Step 2: Connecting Wallet...
  💡 Connect button highlighted in green
  ✅ Wallet connected successfully!
💸 Step 5: Ready for withdrawals!
  ✓ Found 3 contract(s) ready for withdrawal
  ⏳ Browser will stay open for 5 minutes
# ... you click buttons and approve in MetaMask ...
✨ Automation complete!
```

```bash
Terminal 2:
$ cd ..
$ python3 -m http.server 3000
Serving HTTP on 0.0.0.0 port 3000 (http://0.0.0.0:3000/) ...
```

---

## 🎉 That's It!

**One command:**
```bash
npm run web3-automate
```

**Maximum results:**
- Fast wallet connection
- Easy contract management
- Simple withdrawals
- More tokens 💰

---

## 🔗 Next Steps

- Read [README.md](./README.md) for full documentation
- Try `npm run codegen` to record your own automations
- Check out example tests in `tests/example.spec.js`

**Happy automating! 🚀**
