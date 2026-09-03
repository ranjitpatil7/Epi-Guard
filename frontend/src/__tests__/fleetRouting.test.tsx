import { render } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import FleetRouting from '@/pages/logistics/FleetRouting'

vi.mock('@/lib/api/client', () => ({ 
  client: { get: vi.fn(), post: vi.fn() },
  apiClient: { get: vi.fn(), post: vi.fn() },
  __esModule: true
}))

vi.mock('react-leaflet', () => ({
  MapContainer: ({ children }: any) => <div>{children}</div>,
  TileLayer: () => <div></div>,
  Marker: ({ children }: any) => <div>{children}</div>,
  Popup: ({ children }: any) => <div>{children}</div>,
  Polyline: () => <div></div>,
  CircleMarker: () => <div></div>,
  Tooltip: () => <div></div>,
}))

describe('Fleet Routing Integration', () => {
  it('mounts safely without crashing', () => {
    const { container } = render(<FleetRouting />)
    expect(container).toBeTruthy()
  })
})
