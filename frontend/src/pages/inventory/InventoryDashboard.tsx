import { useEffect, useState, useCallback, useRef } from 'react'
import { apiClient } from '@/lib/api/client'
import { Package, AlertTriangle, RefreshCw, TrendingDown, ShieldCheck, Boxes } from 'lucide-react'
import { useRealtime } from '@/hooks/useRealtime'

interface InventoryItem {
  id: number
  name: string
  current_stock: number
  minimum_threshold: number
  unit: string
  is_low_stock: boolean
}

// Visual constants for each supply type
const SUPPLY_META: Record<string, { max: number; color: string; gradient: string; icon: string }> = {
  'ORS Packets': {
    max: 10000,
    color: 'hsl(200, 80%, 55%)',
    gradient: 'linear-gradient(135deg, hsl(200, 80%, 55%), hsl(210, 90%, 45%))',
    icon: '💊'
  },
  'Water Purification Tablets': {
    max: 25000,
    color: 'hsl(160, 70%, 45%)',
    gradient: 'linear-gradient(135deg, hsl(160, 70%, 45%), hsl(170, 80%, 35%))',
    icon: '💧'
  },
  'Vaccines (Cholera)': {
    max: 5000,
    color: 'hsl(35, 90%, 55%)',
    gradient: 'linear-gradient(135deg, hsl(35, 90%, 55%), hsl(25, 85%, 45%))',
    icon: '💉'
  },
}

export default function InventoryDashboard() {
  const [items, setItems] = useState<InventoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const processedEvents = useRef(new Set<string>());
  const { lastEvent } = useRealtime();

  const fetchInventory = useCallback(async () => {
    try {
      setLoading(true)
      const res = await apiClient.get('/inventory/')
      setItems(res.data.items || [])
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch inventory')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchInventory()
    // Polling removed in favor of real-time WebSocket events
  }, [fetchInventory])

  useEffect(() => {
    if (lastEvent && lastEvent.event_type === 'INVENTORY_UPDATED') {
      const msgId = lastEvent.message_id || lastEvent.correlation_id || String(Date.now());
      if (processedEvents.current.has(msgId)) return;
      processedEvents.current.add(msgId);
      
      const payload = lastEvent.payload as any;
      setItems(prev => prev.map(item => 
        item.id === payload.item_id 
          ? { ...item, current_stock: payload.new_stock, is_low_stock: payload.is_low_stock } 
          : item
      ));
    }
  }, [lastEvent]);

  const lowStockCount = items.filter(i => i.is_low_stock).length
  const totalItems = items.reduce((acc, i) => acc + i.current_stock, 0)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-3">
            <Package className="h-7 w-7 text-blue-400" />
            Supply Chain Command
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Real-time central inventory tracking &amp; low-stock alerting
          </p>
        </div>
        <button
          onClick={fetchInventory}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-muted-foreground hover:text-foreground hover:bg-white/10 transition-all"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md p-5">
          <div className="flex items-center gap-3 mb-2">
            <Boxes className="h-5 w-5 text-blue-400" />
            <span className="text-sm text-muted-foreground">Total Supplies</span>
          </div>
          <p className="text-3xl font-bold tracking-tight">{totalItems.toLocaleString()}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md p-5">
          <div className="flex items-center gap-3 mb-2">
            <ShieldCheck className="h-5 w-5 text-emerald-400" />
            <span className="text-sm text-muted-foreground">Items Tracked</span>
          </div>
          <p className="text-3xl font-bold tracking-tight">{items.length}</p>
        </div>
        <div className={`rounded-2xl border p-5 backdrop-blur-md ${lowStockCount > 0 ? 'border-amber-500/30 bg-amber-500/10' : 'border-white/10 bg-white/5'}`}>
          <div className="flex items-center gap-3 mb-2">
            <AlertTriangle className={`h-5 w-5 ${lowStockCount > 0 ? 'text-amber-400' : 'text-muted-foreground'}`} />
            <span className="text-sm text-muted-foreground">Low Stock Alerts</span>
          </div>
          <p className={`text-3xl font-bold tracking-tight ${lowStockCount > 0 ? 'text-amber-400' : ''}`}>{lowStockCount}</p>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Inventory Items */}
      <div className="space-y-4">
        {items.map((item) => {
          const meta = SUPPLY_META[item.name] || { max: item.minimum_threshold * 10, color: 'hsl(220, 60%, 50%)', gradient: 'linear-gradient(135deg, hsl(220,60%,50%), hsl(230,70%,40%))', icon: '📦' }
          const pct = Math.min((item.current_stock / meta.max) * 100, 100)
          const thresholdPct = (item.minimum_threshold / meta.max) * 100

          return (
            <div
              key={item.id}
              className={`rounded-2xl border backdrop-blur-md p-6 transition-all ${item.is_low_stock ? 'border-amber-500/30 bg-amber-500/5' : 'border-white/10 bg-white/5'}`}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{meta.icon}</span>
                  <div>
                    <h3 className="text-lg font-semibold tracking-tight">{item.name}</h3>
                    <p className="text-xs text-muted-foreground">{item.unit}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold tracking-tight" style={{ color: item.is_low_stock ? 'hsl(35, 90%, 55%)' : meta.color }}>
                    {item.current_stock.toLocaleString()}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    of {meta.max.toLocaleString()} capacity
                  </p>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="relative w-full h-4 rounded-full bg-white/5 border border-white/10 overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-700 ease-out"
                  style={{
                    width: `${pct}%`,
                    background: item.is_low_stock ? 'linear-gradient(135deg, hsl(35, 90%, 55%), hsl(0, 80%, 50%))' : meta.gradient,
                    boxShadow: `0 0 12px ${meta.color}40`,
                  }}
                />
                {/* Threshold marker */}
                <div
                  className="absolute top-0 h-full w-0.5 bg-amber-500/60"
                  style={{ left: `${thresholdPct}%` }}
                  title={`Minimum threshold: ${item.minimum_threshold.toLocaleString()}`}
                />
              </div>

              <div className="flex items-center justify-between mt-2 text-xs text-muted-foreground">
                <span>{pct.toFixed(1)}% capacity</span>
                <span className="flex items-center gap-1">
                  <TrendingDown className="h-3 w-3" />
                  Min threshold: {item.minimum_threshold.toLocaleString()} {item.unit}
                </span>
              </div>

              {item.is_low_stock && (
                <div className="mt-3 flex items-center gap-2 rounded-lg bg-amber-500/10 border border-amber-500/20 px-3 py-2 text-amber-400 text-xs font-medium">
                  <AlertTriangle className="h-4 w-4" />
                  LOW STOCK — Below minimum threshold. Replenishment required.
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
