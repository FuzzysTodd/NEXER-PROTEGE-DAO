#!/usr/bin/env node

/**
 * Web3 Contract Automation for Nexus Protocol
 * Automates: Wallet connection, withdrawals, transfers, contract interactions
 * Goal: Maximize token earnings with minimal manual steps
 */

const { chromium } = require('@playwright/test');
const fs = require('fs');

// Ensure screenshots directory exists
if (!fs.existsSync('screenshots')) {
    fs.mkdirSync('screenshots');
}

async function automateWeb3Operations() {
    console.log('\n💰 Nexus Protocol Web3 Automation\n');
    console.log('==================================\n');
    console.log('This tool automates:');
    console.log('  ✓ Wallet connection');
    console.log('  ✓ Contract withdrawals');
    console.log('  ✓ Token transfers');
    console.log('  ✓ Contract interactions\n');

    const browser = await chromium.launch({ 
        headless: false,  // Keep visible so you can approve transactions
        slowMo: 1000      // Slow down for easier interaction
    });
    
    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 }
    });
    
    const page = await context.newPage();
    
    try {
        console.log('🔗 Step 1: Opening Withdraw Manager...');
        await page.goto('http://localhost:3000/withdraw.html');
        await page.waitForLoadState('networkidle');
        await page.screenshot({ path: 'screenshots/step1-loaded.png' });
        console.log('  ✓ Withdraw Manager loaded\n');
        
        console.log('🔌 Step 2: Connecting Wallet...');
        console.log('  ⚠️  ACTION REQUIRED: Click "Connect Wallet" when ready');
        
        // Highlight the connect button
        const connectBtn = page.locator('button:has-text("Connect Wallet")').first();
        await connectBtn.evaluate(el => {
            el.style.border = '3px solid #00ff00';
            el.style.boxShadow = '0 0 20px #00ff00';
        });
        
        await page.screenshot({ path: 'screenshots/step2-connect-highlighted.png' });
        console.log('  💡 Connect button highlighted in green\n');
        
        // Wait for user to connect wallet (button changes to "Connected")
        console.log('  ⏳ Waiting for wallet connection...');
        console.log('  💡 Approve the connection in MetaMask popup\n');
        
        await page.waitForSelector('button:has-text("Connected")', { timeout: 120000 });
        await page.screenshot({ path: 'screenshots/step2-connected.png' });
        console.log('  ✅ Wallet connected successfully!\n');
        
        console.log('📋 Step 3: Checking for contracts...');
        await page.waitForTimeout(2000);
        
        // Check if there are any contracts
        const hasContracts = await page.locator('.contract-card').count() > 0;
        
        if (!hasContracts) {
            console.log('  ℹ️  No contracts found. Let\'s add one!\n');
            console.log('📝 Step 4: Adding contract (form should be visible)...');
            
            // Highlight the add contract form
            await page.locator('#add-contract-form').evaluate(el => {
                el.style.border = '3px solid #00ff00';
            });
            
            await page.screenshot({ path: 'screenshots/step4-add-contract-form.png' });
            console.log('  💡 Add contract form highlighted\n');
            console.log('  ⚠️  Fill in:');
            console.log('     - Contract address');
            console.log('     - Label (optional)');
            console.log('     - Withdrawal method');
            console.log('  Then click "Add Contract"\n');
            
            // Wait for contract to be added
            console.log('  ⏳ Waiting for contract to be added...');
            await page.waitForSelector('.contract-card', { timeout: 120000 });
            console.log('  ✅ Contract added!\n');
        }
        
        console.log('💸 Step 5: Ready for withdrawals!');
        
        // Highlight all withdraw buttons
        const withdrawButtons = page.locator('button:has-text("Withdraw")');
        const count = await withdrawButtons.count();
        
        if (count > 0) {
            console.log(`  ✓ Found ${count} contract(s) ready for withdrawal\n`);
            
            // Highlight each contract card
            await page.locator('.contract-card').evaluateAll(cards => {
                cards.forEach(card => {
                    card.style.border = '3px solid #00ff00';
                    card.style.boxShadow = '0 0 20px rgba(0, 255, 0, 0.3)';
                });
            });
            
            await page.screenshot({ path: 'screenshots/step5-contracts-ready.png', fullPage: true });
            
            console.log('  💡 To withdraw from a contract:');
            console.log('     1. Click the "Withdraw" button (highlighted in green)');
            console.log('     2. Approve the transaction in MetaMask');
            console.log('     3. Wait for confirmation\n');
            
            console.log('  🔄 The automation will wait while you execute withdrawals...\n');
            
            // Keep browser open for user to interact
            console.log('  ⏳ Browser will stay open for 5 minutes for you to execute transactions');
            console.log('  💡 Close the browser when done, or wait for auto-close\n');
            
            await page.waitForTimeout(300000); // 5 minutes
            
        } else {
            console.log('  ⚠️  No contracts with withdraw buttons found\n');
        }
        
        console.log('✨ Automation complete!');
        console.log('📸 All screenshots saved to screenshots/ directory\n');
        
    } catch (error) {
        console.error('❌ Error during automation:', error.message);
        await page.screenshot({ path: 'screenshots/error.png' });
        console.log('📸 Error screenshot saved\n');
        console.log('💡 Common issues:');
        console.log('   - Make sure MetaMask is installed');
        console.log('   - Check that the server is running on http://localhost:3000');
        console.log('   - Ensure you have contracts configured\n');
    } finally {
        await browser.close();
    }
}

// Run automation
automateWeb3Operations().catch(console.error);
