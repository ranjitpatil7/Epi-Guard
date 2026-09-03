import { motion } from 'framer-motion'
import { useQuery } from "@tanstack/react-query"
import { getCurrentRisk } from "@/lib/api/riskApi"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Spinner } from "@/components/ui/spinner"
import { ShieldAlert, Map, AlertTriangle, TrendingUp, Radio, Wifi, WifiOff, RefreshCw } from "lucide-react"
import { BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { IncidentCommandCenter } from "@/components/incidents/IncidentCommandCenter"
import { useRealtime } from "@/hooks/useRealtime"
import { formatDistanceToNow } from "date-fns"

// ─── Connection Status Badge ────────────────────────────────────────────────────

function ConnectionBadge({ status }: { status: string }) {
  const configs: Record<string, { label: string; color: string; Icon: React.FC<any> }> = {
    CONNECTED:    { label: "Live",         color: "text-emerald-400", Icon: Wifi },
    CONNECTING:   { label: "Connecting…",  color: "text-amber-400",   Icon: Radio },
    RECONNECTING: { label: "Reconnecting", color: "text-amber-400",   Icon: RefreshCw },
    DISCONNECTED: { label: "Offline",      color: "text-slate-500",   Icon: WifiOff },
    ERROR:        { label: "Error",        color: "text-red-500",     Icon: WifiOff },
  }
  const { label, color, Icon } = configs[status] ?? configs.DISCONNECTED
  const isLive = status === "CONNECTED"

  return (
    <div className={`flex items-center gap-1.5 text-xs font-medium ${color}`}>
      <span className="relative flex h-2 w-2">
        {isLive && (
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
        )}
        <span className={`relative inline-flex rounded-full h-2 w-2 ${isLive ? "bg-emerald-400" : "bg-slate-500"}`} />
      </span>
      <Icon className="h-3 w-3" />
      {label}
    </div>
  )
}

// ─── Live Event Timeline ────────────────────────────────────────────────────────

function severityColor(severity?: string) {
  switch (severity?.toUpperCase()) {
    case "CRITICAL": return "text-red-400 bg-red-400/10"
    case "HIGH":     return "text-orange-400 bg-orange-400/10"
    case "WARNING":  return "text-amber-400 bg-amber-400/10"
    default:         return "text-slate-400 bg-slate-400/10"
  }
}

function eventLabel(eventType: string) {
  return eventType.replace(/_/g, " ").replace(/INTELLIGENCE /g, "")
}

function LiveTimeline({ events }: { events: Array<{ message_id: string; event_type: string; timestamp: string; region_id?: number; severity?: string }> }) {
  if (events.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-sm text-muted-foreground">
        Waiting for live events…
      </div>
    )
  }
  const recent = [...events].reverse().slice(0, 15)
  return (
    <div className="space-y-1 max-h-64 overflow-y-auto pr-1">
      {recent.map(ev => (
        <div key={ev.message_id} className="flex items-center gap-2 py-1 border-b border-border/40 last:border-0">
          <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${severityColor(ev.severity)}`}>
            {ev.severity ?? "INFO"}
          </span>
          <span className="text-xs font-medium truncate flex-1">{eventLabel(ev.event_type)}</span>
          {ev.region_id != null && (
            <span className="text-[10px] text-muted-foreground">R{ev.region_id}</span>
          )}
          <span className="text-[10px] text-muted-foreground whitespace-nowrap">
            {formatDistanceToNow(new Date(ev.timestamp), { addSuffix: true })}
          </span>
        </div>
      ))}
    </div>
  )
}

// ─── Dashboard ──────────────────────────────────────────────────────────────────

import { containerVariants, itemVariants, chartTooltipStyle, chartColors } from "@/lib/animations"

export default function Dashboard() {
  const { data: riskData, isLoading, error } = useQuery({
    queryKey: ['currentRisk'],
    queryFn: getCurrentRisk,
  })

  const { status, timeline, criticalEventCount } = useRealtime()

  if (isLoading) return <div className="flex h-full items-center justify-center"><Spinner size="lg" /></div>
  if (error) return <div className="text-destructive p-4 bg-destructive/10 rounded-lg">Failed to load dashboard data.</div>

  const totalRegions = riskData?.length || 0
  const highRiskRegions = riskData?.filter(r => r.risk_level === 'HIGH' || r.risk_level === 'CRITICAL').length || 0
  const avgRisk = totalRegions > 0
    ? riskData!.reduce((acc, r) => acc + (r.estimated_risk_score ?? r.risk_score ?? 0), 0) / totalRegions
    : 0

  const distributionMap: Record<string, number> = { LOW: 0, GUARDED: 0, MODERATE: 0, HIGH: 0, CRITICAL: 0 }
  riskData?.forEach(r => {
    if (distributionMap[r.risk_level] !== undefined) {
      distributionMap[r.risk_level]++
    }
  })
  const chartData = [
    { name: 'Low',      count: distributionMap.LOW,      fill: '#10b981' },
    { name: 'Guarded',  count: distributionMap.GUARDED,  fill: '#facc15' },
    { name: 'Mod.',     count: distributionMap.MODERATE, fill: '#eab308' },
    { name: 'High',     count: distributionMap.HIGH,     fill: '#f97316' },
    { name: 'Critical', count: distributionMap.CRITICAL, fill: '#ef4444' },
  ]

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      {/* ── Header ── */}
      <motion.div variants={itemVariants} className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Command Center</h1>
          <p className="text-muted-foreground text-sm">Real-time public health intelligence overview.</p>
        </div>
        <ConnectionBadge status={status} />
      </motion.div>

      {/* ── KPI Cards ── */}
      <motion.div variants={containerVariants} className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[
          { title: "Regions Monitored", value: totalRegions, subtitle: "Across Northeast India", icon: Map, color: "text-blue-400", bg: "bg-blue-500/10" },
          { title: "High/Critical Risk", value: highRiskRegions, subtitle: "Regions require attention", icon: ShieldAlert, color: "text-red-400", bg: "bg-red-500/10" },
          { title: "Live Events", value: timeline.length, subtitle: "Received this session", icon: AlertTriangle, color: "text-amber-400", bg: "bg-amber-500/10", extra: criticalEventCount > 0 ? `(${criticalEventCount} critical)` : "" },
          { title: "Average Risk Index", value: avgRisk.toFixed(1), subtitle: "National average score", icon: TrendingUp, color: "text-emerald-400", bg: "bg-emerald-500/10" }
        ].map((card, i) => (
          <motion.div key={i} variants={itemVariants}>
            <Card className="relative overflow-hidden group">
              <div className={`absolute -right-4 -top-4 w-24 h-24 rounded-full blur-3xl opacity-20 group-hover:opacity-40 transition-opacity duration-500 ${card.bg}`} />
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 relative z-10">
                <CardTitle className="text-sm font-medium text-muted-foreground">{card.title}</CardTitle>
                <div className={`p-2 rounded-xl ${card.bg} border border-white/5`}>
                  <card.icon className={`h-4 w-4 ${card.color}`} />
                </div>
              </CardHeader>
              <CardContent className="relative z-10">
                <div className="text-3xl font-bold tracking-tight text-foreground flex items-baseline gap-2">
                  {card.value}
                  {card.extra && <span className="text-sm font-medium text-red-400">{card.extra}</span>}
                </div>
                <p className="text-xs text-muted-foreground mt-1">{card.subtitle}</p>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.div>

      {/* ── Charts & Top Regions ── */}
      <motion.div variants={itemVariants} className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Regional Risk Distribution</CardTitle>
          </CardHeader>
          <CardContent className="h-[300px] flex items-center justify-center p-6 pt-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                <defs>
                  <linearGradient id="colorLow" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.2}/>
                  </linearGradient>
                  <linearGradient id="colorGuarded" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#facc15" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#facc15" stopOpacity={0.2}/>
                  </linearGradient>
                  <linearGradient id="colorMod" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#eab308" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#eab308" stopOpacity={0.2}/>
                  </linearGradient>
                  <linearGradient id="colorHigh" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f97316" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#f97316" stopOpacity={0.2}/>
                  </linearGradient>
                  <linearGradient id="colorCritical" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.2}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={chartColors.gridLine} vertical={false} />
                <XAxis dataKey="name" stroke="#86868b" tick={{ fontSize: 12, fill: '#86868b' }} axisLine={{ stroke: '#27272a' }} tickLine={false} />
                <YAxis stroke="#86868b" tick={{ fontSize: 12, fill: '#86868b' }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={chartTooltipStyle}
                  itemStyle={{ color: '#e4e4e7', fontWeight: 500 }}
                  labelStyle={{ color: '#a1a1aa', fontWeight: 600, marginBottom: '4px' }}
                  cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }}
                />
                <Bar dataKey="count" name="Regions" radius={[6, 6, 0, 0]} fillOpacity={1}>
                  {chartData.map((_, index) => {
                    const gradients = ['url(#colorLow)', 'url(#colorGuarded)', 'url(#colorMod)', 'url(#colorHigh)', 'url(#colorCritical)'];
                    return <Cell key={`cell-${index}`} fill={gradients[index]} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Highest Risk Regions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {riskData?.sort((a, b) => (b.estimated_risk_score ?? b.risk_score ?? 0) - (a.estimated_risk_score ?? a.risk_score ?? 0)).slice(0, 5).map((region) => (
                <div key={region.region_id} className="flex items-center justify-between">
                  <div className="space-y-1">
                    <p className="text-sm font-medium leading-none text-foreground">{region.region_name}</p>
                    <p className="text-xs text-muted-foreground truncate w-48">
                      {typeof region.contributing_factors?.[0] === 'string' 
                        ? region.contributing_factors[0] 
                        : ((region.contributing_factors?.[0] as any)?.explanation || "Baseline risk")}
                    </p>
                  </div>
                  <div className={`text-sm font-bold ${
                    (region.estimated_risk_score ?? region.risk_score ?? 0) >= 80 ? "text-destructive" :
                    (region.estimated_risk_score ?? region.risk_score ?? 0) >= 60 ? "text-orange-500" :
                    (region.estimated_risk_score ?? region.risk_score ?? 0) >= 40 ? "text-amber-500" : "text-emerald-500"
                  }`}>
                    {region.estimated_risk_score ?? region.risk_score ?? 0} ({region.risk_level})
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* ── Live Event Timeline ── */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-medium">Live Intelligence Timeline</CardTitle>
            <ConnectionBadge status={status} />
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground mb-3 font-medium text-amber-600">
              ⚠️ SYNTHETIC VALIDATION DATA — NON-DIAGNOSTIC DECISION SUPPORT ONLY
            </p>
            <LiveTimeline events={timeline} />
          </CardContent>
        </Card>
      </motion.div>

      {/* ── Incident Command Center ── */}
      <motion.div variants={itemVariants} className="grid gap-4 mt-6">
        <IncidentCommandCenter />
      </motion.div>
    </motion.div>
  )
}
