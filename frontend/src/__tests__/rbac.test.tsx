import { render } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { ProtectedRoute } from '../../src/components/auth/ProtectedRoute'
import * as AuthContextModule from '../../src/lib/auth/AuthContext'

vi.mock('../../src/lib/auth/AuthContext', () => ({
  useAuth: vi.fn(),
}))

const TestComponent = () => <div data-testid="protected">Protected Content</div>

describe('ProtectedRoute Integration', () => {
  it('redirects to /login if unauthenticated', () => {
    vi.mocked(AuthContextModule.useAuth).mockReturnValue({
      user: null,
      hasPermission: () => false,
      isAuthenticated: false,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
    } as any)

    const { container } = render(
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route path="/admin" element={<TestComponent />} />
          </Route>
        </Routes>
      </MemoryRouter>
    )

    expect(container).toBeTruthy()
  })

  it('renders protected content if authenticated', () => {
    vi.mocked(AuthContextModule.useAuth).mockReturnValue({
      user: { id: 1, role: 'National_Command', username: 'admin', full_name: 'Admin', region_id: 1, status: 'active', permissions: [] },
      hasPermission: () => true,
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
    } as any)

    const { container } = render(
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route path="/admin" element={<TestComponent />} />
          </Route>
        </Routes>
      </MemoryRouter>
    )

    expect(container).toBeTruthy()
  })
})
