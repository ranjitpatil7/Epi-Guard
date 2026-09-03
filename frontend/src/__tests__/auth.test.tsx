import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { AuthProvider, useAuth } from '@/lib/auth/AuthContext'
import axios from 'axios'
import userEvent from '@testing-library/user-event'

// Mock axios
vi.mock('axios', () => {
  const mockInstance = {
    get: vi.fn(),
    post: vi.fn(),
    interceptors: {
      request: { use: vi.fn(), eject: vi.fn() },
      response: { use: vi.fn(), eject: vi.fn() }
    }
  }
  return {
    default: {
      ...mockInstance,
      create: vi.fn(() => mockInstance)
    }
  }
})

// Test Component that consumes AuthContext
function TestComponent() {
  const { user, isAuthenticated, isLoading, login, logout } = useAuth()
  
  if (isLoading) return <div>Loading Auth...</div>
  
  return (
    <div>
      <div data-testid="auth-status">{isAuthenticated ? 'Authenticated' : 'Unauthenticated'}</div>
      <div data-testid="user-role">{user ? user.role : 'None'}</div>
      <button onClick={() => login('mock_access', 'mock_refresh', 'mock_session')}>Login</button>
      <button onClick={() => logout()}>Logout</button>
    </div>
  )
}

describe('AuthContext Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders unauthenticated state initially when no token exists', async () => {
    render(<AuthProvider><TestComponent /></AuthProvider>)
    expect(screen.getByTestId('auth-status')).toHaveTextContent('Unauthenticated')
  })

  it('fetches user and sets authenticated state if token exists in localStorage', async () => {
    localStorage.setItem('access_token', 'fake_token')
    
    // Mock the /me response exactly matching backend
    vi.mocked(axios.get).mockResolvedValueOnce({
      data: {
        id: 1,
        username: 'admin_test',
        role: 'Administrator',
        region_id: null,
        permissions: ['MANAGE_USERS', 'VIEW_RISK']
      }
    })

    render(<AuthProvider><TestComponent /></AuthProvider>)
    
    expect(screen.getByText('Loading Auth...')).toBeInTheDocument()
    
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated')
      expect(screen.getByTestId('user-role')).toHaveTextContent('Administrator')
    })
  })

  it('handles login function and fetches user', async () => {
    vi.mocked(axios.get).mockResolvedValueOnce({
      data: { id: 2, role: 'Field Officer', permissions: [] }
    })

    render(<AuthProvider><TestComponent /></AuthProvider>)
    
    const loginButton = screen.getByText('Login')
    await userEvent.click(loginButton)

    expect(localStorage.getItem('access_token')).toBe('mock_access')
    
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated')
      expect(screen.getByTestId('user-role')).toHaveTextContent('Field Officer')
    })
  })

  it('handles logout function and clears state', async () => {
    // Setup initial auth state
    localStorage.setItem('access_token', 'fake')
    localStorage.setItem('session_id', 'sess1')
    
    vi.mocked(axios.get).mockResolvedValueOnce({
      data: { id: 1, role: 'Admin', permissions: [] }
    })
    
    vi.mocked(axios.post).mockResolvedValueOnce({})

    render(<AuthProvider><TestComponent /></AuthProvider>)
    
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated')
    })

    const logoutButton = screen.getByText('Logout')
    await userEvent.click(logoutButton)

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Unauthenticated')
      expect(localStorage.getItem('access_token')).toBeNull()
    })
    
    // Should call logout endpoint
    expect(axios.post).toHaveBeenCalledWith('/api/v1/auth/logout?session_id=sess1')
  })
})

