#!/bin/bash

##############################################################################
# Nexus Protocol Web3 Automation Tool - One-Click Installer
# Reduces setup to minimal steps for maximum ease of use
##############################################################################

echo ""
echo "💰 Nexus Protocol Web3 Automation Tool"
echo "======================================"
echo ""
echo "This tool helps you:"
echo "  ✓ Withdraw from contracts automatically"
echo "  ✓ Transfer tokens with ease"
echo "  ✓ Interact with Nexus contracts"
echo "  ✓ Maximize token earnings"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    echo "📥 Please install Node.js from: https://nodejs.org/"
    echo ""
    exit 1
fi

echo "✓ Node.js found: $(node --version)"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "🌐 Installing Chromium browser..."
npm run install-browsers

if [ $? -ne 0 ]; then
    echo "⚠️  Browser installation failed, but you can continue"
fi

# Create necessary directories
echo ""
echo "📁 Creating directories..."
mkdir -p screenshots
mkdir -p test-results

echo ""
echo "✅ Installation complete!"
echo ""
echo "🚀 Quick Start Commands:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  1. Start the server (in another terminal):"
echo "     cd .. && python3 -m http.server 3000"
echo ""
echo "  2. Run Web3 automation:"
echo "     npm run web3-automate"
echo ""
echo "  3. Run quick test:"
echo "     npm run quick-start"
echo ""
echo "  4. Run full test suite:"
echo "     npm test"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Tip: The web3-automate command will help you:"
echo "   - Connect your wallet"
echo "   - Withdraw from contracts"
echo "   - Transfer tokens"
echo ""
echo "📚 See README.md for more details"
echo ""
