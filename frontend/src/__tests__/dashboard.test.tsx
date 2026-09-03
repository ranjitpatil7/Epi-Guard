import { render } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import Dashboard from '@/pages/dashboard/Dashboard'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('@/lib/api/client', () => ({ 
  client: { get: vi.fn(), post: vi.fn() },
  apiClient: { get: vi.fn(), post: vi.fn() },
  __esModule: true
}))

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })

describe('Dashboard Component Integration', () => {
  it('mounts safely without crashing', () => {
    const { container } = render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <Dashboard />
        </MemoryRouter>
      </QueryClientProvider>
    )
    expect(container).toBeTruthy()
  })
})
