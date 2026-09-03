import { render } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import InventoryDashboard from '@/pages/inventory/InventoryDashboard'

vi.mock('@/lib/api/client', () => ({ 
  client: { get: vi.fn(), post: vi.fn() },
  apiClient: { get: vi.fn(), post: vi.fn() },
  __esModule: true
}))
vi.mock('@/hooks/useRealtime', () => ({ 
  useRealtime: vi.fn(() => ({ lastEvent: null })) 
}))

describe('Inventory Dashboard Integration', () => {
  it('mounts safely without crashing', () => {
    const { container } = render(<InventoryDashboard />)
    expect(container).toBeTruthy()
  })
})
