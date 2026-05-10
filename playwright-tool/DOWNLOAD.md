# 📥 How to Download and Use Nexus Playwright Tool

## Option 1: Clone the Repository (Recommended)

```bash
git clone https://github.com/FuzzysTodd/The-Nexus-Protocol-Token-DOA.git
cd The-Nexus-Protocol-Token-DOA/playwright-tool
./install.sh
```

## Option 2: Download as ZIP

1. Go to: https://github.com/FuzzysTodd/The-Nexus-Protocol-Token-DOA
2. Click "Code" → "Download ZIP"
3. Extract the ZIP file
4. Navigate to the `playwright-tool` folder
5. Run `./install.sh`

## Option 3: Download Just the Tool

```bash
# Download the playwright-tool directory only
svn export https://github.com/FuzzysTodd/The-Nexus-Protocol-Token-DOA/trunk/playwright-tool

cd playwright-tool
./install.sh
```

## Quick Setup After Download

```bash
# 1. Install dependencies
cd playwright-tool
./install.sh

# 2. Start server (in one terminal)
cd ..
python3 -m http.server 3000

# 3. Run automation (in another terminal)
cd playwright-tool
npm run web3-automate
```

## System Requirements

- **Node.js** v16 or higher - [Download](https://nodejs.org/)
- **Python 3** for local server
- **Chrome/Chromium** browser (auto-installed)
- **MetaMask** extension (for Web3 features)

## What You Get

✅ Complete automation tool  
✅ Pre-configured for Nexus Protocol  
✅ One-command installation  
✅ Web3 contract interaction automation  
✅ Withdrawal automation  
✅ Multiple example scripts  

## Need Help?

See [README.md](./README.md) for full documentation.
