import { render } from '@testing-library/react'
import { AuthProvider } from '../contexts/AuthContext'

// Create a custom render function that includes providers
export function renderWithProviders(ui, options = {}) {
  function Wrapper({ children }) {
    return (
      <AuthProvider>
        {children}
      </AuthProvider>
    )
  }
  
  return render(ui, { wrapper: Wrapper, ...options })
}

// Mock auth context for easier testing
export const createMockAuthContext = (overrides = {}) => ({
  user: null,
  token: null,
  loading: false,
  login: vi.fn(),
  logout: vi.fn(),
  register: vi.fn(),
  authenticatedFetch: vi.fn(),
  ...overrides
})