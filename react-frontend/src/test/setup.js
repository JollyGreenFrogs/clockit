import '@testing-library/jest-dom'

// Global test setup
beforeEach(() => {
  // Clear localStorage before each test
  localStorage.clear()
  
  // Mock window.matchMedia
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation(query => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(), // deprecated
      removeListener: vi.fn(), // deprecated
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  })
})

// Mock fetch for API calls
global.fetch = vi.fn()

afterEach(() => {
  vi.clearAllMocks()
})