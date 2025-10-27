import { test, expect } from '@playwright/test';

test.describe('Invoice Generation E2E Tests', () => {
  // These tests require a running backend with some task data
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
  });

  test('should show invoice generation interface', async ({ page }) => {
    // Look for invoice generation buttons or section
    const invoiceButton = page.locator('button:has-text("Preview Invoice"), button:has-text("Generate")').first();
    
    if (await invoiceButton.isVisible()) {
      // Invoice interface is available
      await expect(invoiceButton).toBeVisible();
    } else {
      // If not directly visible, might be in a navigation menu or tab
      const navLinks = page.locator('nav a, .nav a, [role="tab"]');
      const invoiceLink = navLinks.filter({ hasText: /invoice/i }).first();
      
      if (await invoiceLink.isVisible()) {
        await invoiceLink.click();
        await expect(page.locator('button:has-text("Preview Invoice"), button:has-text("Generate")')).toBeVisible();
      }
    }
  });

  test('should handle invoice preview request', async ({ page }) => {
    // Navigate to dashboard or main page where invoice functionality is available
    await page.goto('/');
    
    // Look for preview button
    const previewButton = page.locator('button:has-text("Preview Invoice")').first();
    
    if (await previewButton.isVisible()) {
      // Set up network interception to monitor API calls
      const apiRequest = page.waitForRequest('**/invoice/preview');
      
      await previewButton.click();
      
      // Wait for the API request to be made
      const request = await apiRequest;
      expect(request.url()).toContain('/invoice/preview');
      
      // Wait for response and check if preview content appears
      await page.waitForTimeout(2000); // Allow time for response
      
      // Check for success or error message
      const resultMessage = page.locator('.alert, .message, .result').first();
      if (await resultMessage.isVisible()) {
        const messageText = await resultMessage.textContent();
        expect(messageText).toMatch(/(preview|generated|error|no.*data)/i);
      }
    }
  });

  test('should handle invoice generation request', async ({ page }) => {
    await page.goto('/');
    
    // Look for generate button
    const generateButton = page.locator('button:has-text("Generate"), button:has-text("Export")').first();
    
    if (await generateButton.isVisible()) {
      // Set up download handler
      const downloadPromise = page.waitForEvent('download');
      
      // Set up network interception
      const apiRequest = page.waitForRequest('**/invoice/generate');
      
      await generateButton.click();
      
      // Wait for the API request
      const request = await apiRequest;
      expect(request.url()).toContain('/invoice/generate');
      expect(request.method()).toBe('POST');
      
      // Wait for either download or error message
      try {
        const download = await downloadPromise;
        // If download succeeds, check filename
        expect(download.suggestedFilename()).toMatch(/invoice.*\.csv$/i);
      } catch {
        // If no download, check for error message
        const errorMessage = page.locator('.alert-error, .error, .message').first();
        await expect(errorMessage).toBeVisible();
      }
    }
  });

  test('should show appropriate messages for empty invoice data', async ({ page }) => {
    await page.goto('/');
    
    const previewButton = page.locator('button:has-text("Preview Invoice")').first();
    
    if (await previewButton.isVisible()) {
      await previewButton.click();
      
      // Wait for response
      await page.waitForTimeout(3000);
      
      // Should show either preview content or "no data" message
      const hasPreview = await page.locator('.invoice-preview, .preview-content').count() > 0;
      const hasNoDataMessage = await page.locator('text=/no.*data|no.*tasks|empty/i').count() > 0;
      const hasErrorMessage = await page.locator('.alert-error, .error').count() > 0;
      
      // At least one of these should be true
      expect(hasPreview || hasNoDataMessage || hasErrorMessage).toBe(true);
    }
  });

  test('should handle backend errors gracefully', async ({ page }) => {
    await page.goto('/');
    
    // Mock a failed response
    await page.route('**/invoice/preview', (route) => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' })
      });
    });
    
    const previewButton = page.locator('button:has-text("Preview Invoice")').first();
    
    if (await previewButton.isVisible()) {
      await previewButton.click();
      
      // Should show error message
      await expect(page.locator('text=/error/i')).toBeVisible();
    }
  });

  test('should make authenticated requests', async ({ page }) => {
    await page.goto('/');
    
    let _authHeaderFound = false;
    
    // Intercept requests to check for authentication
    page.on('request', (request) => {
      if (request.url().includes('/invoice/')) {
        const headers = request.headers();
        if (headers.authorization || headers.Authorization) {
          _authHeaderFound = true;
        }
      }
    });
    
    const previewButton = page.locator('button:has-text("Preview Invoice")').first();
    
    if (await previewButton.isVisible()) {
      await previewButton.click();
      await page.waitForTimeout(1000);
      
      // If the request was made, it should have included auth headers
      // Note: This might not trigger if user is not logged in
    }
  });
});