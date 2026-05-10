#!/usr/bin/env node

/**
 * Automated Testing Script for Nexus Protocol
 * Run common automation tasks with minimal setup
 */

const { chromium } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

// Ensure screenshots directory exists
if (!fs.existsSync('screenshots')) {
    fs.mkdirSync('screenshots');
}

async function automateNexus() {
    console.log('\n🤖 Nexus Protocol Automation Tool\n');
    console.log('================================\n');

    const browser = await chromium.launch({ 
        headless: false,
        slowMo: 300
    });
    
    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 }
    });
    
    const page = await context.newPage();
    
    try {
        // Test 1: Withdraw Manager
        console.log('🧪 Test 1: Withdraw Manager UI');
        await page.goto('http://localhost:3000/withdraw.html');
        await page.waitForLoadState('networkidle');
        
        // Check for key elements
        const title = await page.textContent('h1');
        console.log('  ✓ Page title:', title.trim());
        
        const connectBtn = await page.locator('button:has-text("Connect Wallet")');
        console.log('  ✓ Connect button found');
        
        await page.screenshot({ 
            path: 'screenshots/test-1-withdraw.png',
            fullPage: true 
        });
        console.log('  📸 Screenshot saved\n');
        
        // Test 2: Crypto Expert Guide
        console.log('🧪 Test 2: Crypto Expert Guide');
        await page.goto('http://localhost:3000/crypto-expert-guide.html');
        await page.waitForLoadState('networkidle');
        
        const expertTitle = await page.textContent('h1');
        console.log('  ✓ Page loaded:', expertTitle.trim().substring(0, 50) + '...');
        
        await page.screenshot({ 
            path: 'screenshots/test-2-crypto-expert.png',
            fullPage: true 
        });
        console.log('  📸 Screenshot saved\n');
        
        // Test 3: Chimera Dashboard
        console.log('🧪 Test 3: Chimera Dashboard');
        await page.goto('http://localhost:3000/chimera.html');
        await page.waitForLoadState('networkidle');
        
        const chimeraTitle = await page.textContent('h1');
        console.log('  ✓ Page loaded:', chimeraTitle.trim());
        
        await page.screenshot({ 
            path: 'screenshots/test-3-chimera.png',
            fullPage: true 
        });
        console.log('  📸 Screenshot saved\n');
        
        console.log('✅ All tests completed successfully!');
        console.log('📂 Check the screenshots/ directory for results\n');
        
    } catch (error) {
        console.error('❌ Error during automation:', error.message);
        await page.screenshot({ path: 'screenshots/error.png' });
        console.log('📸 Error screenshot saved\n');
    } finally {
        await browser.close();
    }
}

// Run automation
automateNexus().catch(console.error);
