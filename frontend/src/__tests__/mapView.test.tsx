import { render } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import MapView from '@/pages/map/MapView'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

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
  Polygon: () => <div></div>,
  CircleMarker: () => <div></div>,
  Tooltip: () => <div></div>,
  useMap: vi.fn(() => ({ setView: vi.fn() })),
}))

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })

describe('MapView Component Integration', () => {
  it('mounts safely without crashing', () => {
    const { container } = render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <MapView />
        </MemoryRouter>
      </QueryClientProvider>
    )
    expect(container).toBeTruthy()
  })
})
