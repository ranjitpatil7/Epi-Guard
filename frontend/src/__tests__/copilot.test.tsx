import { render } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import Copilot from '@/pages/copilot/Copilot'

vi.mock('@/lib/api/client', () => ({ 
  client: { get: vi.fn(), post: vi.fn() },
  apiClient: { get: vi.fn(), post: vi.fn() },
  __esModule: true
}))

vi.mock('react-markdown', () => ({
  default: ({ children }: any) => <div>{children}</div>
}))

describe('Copilot Integration', () => {
  it('mounts safely without crashing', () => {
    const { container } = render(<Copilot />)
    expect(container).toBeTruthy()
  })
})
