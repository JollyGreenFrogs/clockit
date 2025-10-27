# Testing Guide for ClockIt Frontend

This project uses a comprehensive testing strategy with two main testing frameworks:

## Testing Tools

### 1. Vitest (Component Testing)
- **Purpose**: Unit and integration testing for React components
- **Environment**: jsdom (simulates browser environment)
- **Test Files**: `src/**/*.test.{js,jsx,ts,tsx}`

### 2. Playwright (E2E Testing)
- **Purpose**: End-to-end testing of complete user workflows
- **Environment**: Real browsers (Chromium, Firefox, WebKit)
- **Test Files**: `e2e/**/*.spec.js`
- **WSL Compatible**: Configured for headless mode

## Running Tests

### Component Tests (Vitest)
```bash
# Run tests in watch mode
npm run test

# Run tests once
npm run test:run

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

### E2E Tests (Playwright)
```bash
# Run all E2E tests
npm run test:e2e

# Run E2E tests with UI
npm run test:e2e:ui

# Debug E2E tests
npm run test:e2e:debug

# Install Playwright browsers
npm run playwright:install
```

### All Tests
```bash
# Run both component and E2E tests
npm run test:run && npm run test:e2e
```

## Test Structure

### Component Tests
- Located in `src/components/__tests__/`
- Use `@testing-library/react` for rendering and interaction
- Mock external dependencies and API calls
- Test component behavior and user interactions

### E2E Tests
- Located in `e2e/`
- Test complete user workflows
- Run against real browser instances
- Test integration between frontend and backend

## Configuration Files

- `vite.config.js` - Vitest configuration
- `playwright.config.js` - Playwright configuration
- `src/test/setup.js` - Test setup and global mocks
- `src/test/test-utils.jsx` - Custom testing utilities

## WSL Considerations

All tests are configured to run in headless mode for compatibility with WSL environments:
- Playwright uses headless browsers
- No GUI dependencies required
- Suitable for CI/CD pipelines

## Best Practices

1. **Component Tests**: Focus on component behavior, not implementation details
2. **E2E Tests**: Test critical user paths and workflows
3. **Mocking**: Mock external APIs and services appropriately
4. **Assertions**: Use descriptive test names and assertions
5. **Clean Up**: Tests automatically clean up between runs

## Example Test Commands

```bash
# Test specific component
npm run test Login

# Test specific E2E scenario
npx playwright test --grep "authentication"

# Run tests with verbose output
npm run test -- --reporter=verbose

# Generate coverage report
npm run test:coverage
```