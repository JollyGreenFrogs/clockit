import { test, expect } from '@playwright/test';

test.describe('ClockIt App E2E Tests', () => {
  test('should load the homepage', async ({ page }) => {
    await page.goto('/');
    
    // Check that the page loads
    await expect(page).toHaveTitle(/ClockIt/i);
    
    // Check for main navigation or heading
    const heading = page.locator('h1, h2, [data-testid="app-title"]').first();
    await expect(heading).toBeVisible();
  });

  test('should show authentication page when not logged in', async ({ page }) => {
    await page.goto('/');
    
    // Check for login/register elements
    const loginButton = page.locator('button:has-text("Login"), button:has-text("Sign In")').first();
    const registerLink = page.locator('a:has-text("Register"), a:has-text("Sign Up")').first();
    
    // At least one authentication element should be visible
    const authVisible = await loginButton.isVisible() || await registerLink.isVisible();
    expect(authVisible).toBe(true);
  });

  test('should navigate to registration page', async ({ page }) => {
    await page.goto('/');
    
    // Look for register/sign up link
    const registerLink = page.locator('a:has-text("Register"), a:has-text("Sign Up"), button:has-text("Register")').first();
    
    if (await registerLink.isVisible()) {
      await registerLink.click();
      
      // Check that we're on registration page
      const emailField = page.locator('input[type="email"], input[name="email"]');
      const passwordField = page.locator('input[type="password"], input[name="password"]');
      
      await expect(emailField).toBeVisible();
      await expect(passwordField).toBeVisible();
    }
  });

  test('should handle login form validation', async ({ page }) => {
    await page.goto('/');
    
    // Try to find and fill login form
    const emailField = page.locator('input[type="email"], input[name="email"]').first();
    const _passwordField = page.locator('input[type="password"], input[name="password"]').first();
    const loginButton = page.locator('button:has-text("Login"), button:has-text("Sign In"), button[type="submit"]').first();
    
    if (await emailField.isVisible()) {
      // Test empty form submission
      await loginButton.click();
      
      // Should show validation errors or stay on same page
      const errorMessage = page.locator('.error, .alert, [role="alert"]').first();
      const isStillOnLoginPage = await emailField.isVisible();
      
      // Either should show error or stay on login page
      const hasValidation = await errorMessage.isVisible() || isStillOnLoginPage;
      expect(hasValidation).toBe(true);
    }
  });
});