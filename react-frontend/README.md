# ClockIt Frontend

React + Vite frontend for the ClockIt time tracking application.

## Features

- ⚡️ **Fast Development**: Vite with Hot Module Replacement (HMR)
- 🧪 **Comprehensive Testing**: Vitest + Playwright for component and E2E testing
- 🔒 **Authentication**: JWT-based authentication with context management
- 📱 **Responsive Design**: Mobile-friendly time tracking interface
- 🎯 **Task Management**: Create, track, and manage time entries
- 💰 **Rate Configuration**: Flexible hourly rate management
- 📊 **Invoice Generation**: Export time tracking data

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Testing

This project includes comprehensive testing with both component and end-to-end tests.

### Component Tests (Vitest)
```bash
npm run test          # Watch mode
npm run test:run      # Single run
npm run test:coverage # With coverage
```

### E2E Tests (Playwright)
```bash
npm run test:e2e      # Run E2E tests
npm run test:e2e:ui   # With UI
```

📖 **See [TESTING.md](./TESTING.md) for detailed testing guide**

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run test` - Run component tests
- `npm run test:e2e` - Run E2E tests

### WSL Compatibility

All tests are configured for headless operation, making them fully compatible with WSL environments.

## Tech Stack

- **React 19** - UI library with latest features
- **Vite** - Fast build tool and dev server
- **Vitest** - Fast unit testing framework
- **Playwright** - Reliable E2E testing
- **Testing Library** - Simple component testing utilities
