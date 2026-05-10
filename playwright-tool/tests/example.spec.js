const { test, expect } = require('@playwright/test');

/**
 * Example Playwright Tests for Nexus Protocol
 * These tests demonstrate how to use the tool
 */

test.describe('Nexus Protocol Pages', () => {
    
    test('should load withdraw manager', async ({ page }) => {
        await page.goto('/withdraw.html');
        
        // Check page title
        await expect(page).toHaveTitle(/Contract Withdrawal Manager/);
        
        // Check for main heading
        const heading = page.locator('h1');
        await expect(heading).toContainText('Contract Withdrawal Manager');
        
        // Check for connect button
        const connectBtn = page.locator('button:has-text("Connect Wallet")');
        await expect(connectBtn).toBeVisible();
        
        // Take a screenshot
        await page.screenshot({ path: 'test-results/withdraw.png' });
    });
    
    test('should load crypto expert guide', async ({ page }) => {
        await page.goto('/crypto-expert-guide.html');
        
        // Wait for page to load
        await page.waitForLoadState('networkidle');
        
        // Check for main heading
        const heading = page.locator('h1');
        await expect(heading).toBeVisible();
        
        // Take a screenshot
        await page.screenshot({ path: 'test-results/crypto-expert.png' });
    });
    
    test('should load chimera dashboard', async ({ page }) => {
        await page.goto('/chimera.html');
        
        // Wait for page to load
        await page.waitForLoadState('networkidle');
        
        // Check for main heading
        const heading = page.locator('h1');
        await expect(heading).toContainText('Nexus Protocol');
        
        // Take a screenshot
        await page.screenshot({ path: 'test-results/chimera.png' });
    });
    
});
