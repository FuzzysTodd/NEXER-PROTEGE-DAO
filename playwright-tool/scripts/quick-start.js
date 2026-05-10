#!/usr/bin/env node

/**
 * Quick Start Script for Nexus Playwright Tool
 * Simplified automation with minimal steps
 */

const { chromium } = require('@playwright/test');
const path = require('path');

async function quickStart() {
    console.log('\n🚀 Nexus Playwright Quick Start\n');
    console.log('Starting automated browser session...\n');

    const browser = await chromium.launch({ 
        headless: false,
        slowMo: 500  // Slow down for visibility
    });
    
    const context = await browser.newContext({
        viewport: { width: 1280, height: 720 }
    });
    
    const page = await context.newPage();
    
    try {
        // Navigate to the local server
        console.log('📍 Navigating to Nexus Protocol pages...');
        await page.goto('http://localhost:3000/withdraw.html');
        await page.waitForLoadState('networkidle');
        
        console.log('✓ Loaded withdraw.html');
        await page.screenshot({ path: 'screenshots/withdraw-page.png' });
        
        // Wait for user to see the page
        await page.waitForTimeout(2000);
        
        // Try the crypto expert guide
        console.log('\n📍 Navigating to crypto expert guide...');
        await page.goto('http://localhost:3000/crypto-expert-guide.html');
        await page.waitForLoadState('networkidle');
        
        console.log('✓ Loaded crypto-expert-guide.html');
        await page.screenshot({ path: 'screenshots/crypto-expert.png' });
        
        await page.waitForTimeout(2000);
        
        console.log('\n✨ Quick start complete!');
        console.log('📸 Screenshots saved to screenshots/ directory');
        console.log('\n💡 Tip: Check the screenshots to see what was captured!');
        
    } catch (error) {
        console.error('❌ Error:', error.message);
        console.log('\n💡 Make sure the server is running on http://localhost:3000');
        console.log('   Run: cd .. && python3 -m http.server 3000');
    } finally {
        await browser.close();
    }
}

// Run the quick start
quickStart().catch(console.error);
