import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import userEvent from '@testing-library/user-event'
import SIRForecast from '../pages/forecasting/SIRForecast'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const mockGet = vi.fn()

vi.mock('@/lib/api/client', () => ({
  client: { get: (...args: any[]) => mockGet(...args), post: vi.fn() },
  apiClient: { get: (...args: any[]) => mockGet(...args), post: vi.fn() },
  __esModule: true
}))

vi.mock('../lib/api/client', () => ({
  client: { get: (...args: any[]) => mockGet(...args), post: vi.fn() },
  apiClient: { get: (...args: any[]) => mockGet(...args), post: vi.fn() },
  __esModule: true
}))

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  LineChart: ({ children }: any) => <div>{children}</div>,
  Line: () => <div></div>,
  XAxis: () => <div></div>,
  YAxis: () => <div></div>,
  CartesianGrid: () => <div></div>,
  Tooltip: () => <div></div>,
  Legend: () => <div></div>,
}))

describe('SIR Forecast Component Behavior', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    vi.resetAllMocks()
    
    mockGet.mockImplementation(async (url: string) => {
      if (url && url.includes('/regions')) {
        return { data: [
          { id: 999, name: 'Test Region A', lat: 10, lng: 10 },
          { id: 888, name: 'Test Region B', lat: 20, lng: 20 }
        ]}
      }
      return { 
        data: { 
          parameters: { R0: 1.5 },
          insights: { peak_infection_day: 10, peak_infected_count: 500, herd_immunity_threshold: "60%" },
          forecast: [] 
        } 
      }
    })
  })

  it('verifies dynamic region loading, selection, and API request', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <SIRForecast />
      </QueryClientProvider>
    )

    // 1. Verify getRegions() was called
    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith('/regions/')
    })

    // 2. Verify returned database regions appear
    await waitFor(() => {
      expect(screen.getByText('Test Region A')).toBeTruthy()
      expect(screen.getByText('Test Region B')).toBeTruthy()
    })

    // 3. Verify NO hardcoded region IDs are present (e.g. 1 through 8)
    const options = screen.getAllByRole('option')
    const values = options.map(opt => (opt as HTMLOptionElement).value)
    expect(values).not.toContain('1')
    expect(values).not.toContain('2')
    expect(values).toContain('999')
    expect(values).toContain('888')

    // 4. Verify selecting a region triggers correct SIR API
    const select = screen.getByRole('combobox')
    await userEvent.selectOptions(select, '888')

    await waitFor(() => {
      // It should call /forecasting/sir/888 with beta/gamma default query params
      expect(mockGet).toHaveBeenCalledWith(expect.stringContaining('/forecasting/sir/888'))
    })
  })
})
