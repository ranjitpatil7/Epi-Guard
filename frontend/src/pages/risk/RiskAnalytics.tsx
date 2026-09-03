import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { getCurrentRisk } from "@/lib/api/riskApi"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Spinner } from "@/components/ui/spinner"
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from "recharts"
import { motion } from "framer-motion"
import { containerVariants, itemVariants, chartTooltipStyle, chartColors } from "@/lib/animations"

import { RiskSnapshotTimeline } from "@/components/risk/RiskSnapshotTimeline"
import { RiskExplanationPanel } from "@/components/risk/RiskExplanationPanel"

export default function RiskAnalytics() {
  const { data: riskData, isLoading } = useQuery({
    queryKey: ['currentRisk'],
    queryFn: getCurrentRisk
  })

  // State to hold selected region for explanation
  const [selectedRegionId, setSelectedRegionId] = useState<number | null>(null)

  if (isLoading) {
    return <div className="flex h-full items-center justify-center"><Spinner size="lg" /></div>
  }

  // Prepare data for distribution pie chart
  const distributionMap: Record<string, number> = { LOW: 0, GUARDED: 0, MODERATE: 0, HIGH: 0, CRITICAL: 0 }
  riskData?.forEach(r => {
    if (distributionMap[r.risk_level] !== undefined) {
      distributionMap[r.risk_level]++
    }
  })

  const pieData = [
    { name: 'Low', value: distributionMap.LOW, color: chartColors.emerald },
    { name: 'Guarded', value: distributionMap.GUARDED, color: chartColors.amber },
    { name: 'Moderate', value: distributionMap.MODERATE, color: '#eab308' },
    { name: 'High', value: distributionMap.HIGH, color: '#f97316' },
    { name: 'Critical', value: distributionMap.CRITICAL, color: chartColors.rose },
  ].filter(d => d.value > 0)

  // Sort by risk score
  const sortedRiskData = riskData ? [...riskData].sort((a, b) => {
    const scoreA = a.estimated_risk_score ?? a.risk_score ?? 0
    const scoreB = b.estimated_risk_score ?? b.risk_score ?? 0
    return scoreB - scoreA
  }) : []

  // Prepare data for bar chart (top 10 highest risk)
  const barData = sortedRiskData
    .slice(0, 10)
    .map(r => ({
      name: r.region_name,
      score: r.estimated_risk_score ?? r.risk_score ?? 0,
      regionId: r.region_id
    }))

  // Determine which region to show explanation for (default highest risk)
  const activeRegion = selectedRegionId 
    ? sortedRiskData.find(r => r.region_id === selectedRegionId) 
    : sortedRiskData[0] as any

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      <motion.div variants={itemVariants}>
        <h1 className="text-3xl font-bold tracking-tight">Risk Analytics</h1>
        <p className="text-muted-foreground text-sm">Visual analysis of regional risk distributions and trends.</p>
      </motion.div>

      {/* XAI Explanation Panel */}
      {activeRegion && (
        <motion.div variants={itemVariants}>
          <RiskExplanationPanel 
            riskScore={activeRegion.estimated_risk_score ?? activeRegion.risk_score ?? 0} 
            riskLevel={activeRegion.risk_level} 
            contributingFactors={activeRegion.contributing_factors as any}
          />
        </motion.div>
      )}

      <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Risk Level Distribution</CardTitle>
          </CardHeader>
          <CardContent className="h-[350px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={80}
                  outerRadius={120}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, percent }) => percent !== undefined ? `${name} ${(percent * 100).toFixed(0)}%` : name}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke="transparent" />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={chartTooltipStyle}
                  itemStyle={{ color: '#1d1d1f' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Highest Risk Regions (Click to Inspect)</CardTitle>
          </CardHeader>
          <CardContent className="h-[350px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart 
                data={barData} 
                layout="vertical" 
                margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
                onClick={(data: any) => {
                  if (data && data.activePayload && data.activePayload.length > 0) {
                    setSelectedRegionId(data.activePayload[0].payload.regionId)
                  }
                }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke={chartColors.gridLine} horizontal={false} />
                <XAxis type="number" domain={[0, 100]} stroke="#86868b" tick={{ fontSize: 12, fill: '#86868b' }} axisLine={{ stroke: '#e5e5ea' }} tickLine={false} />
                <YAxis dataKey="name" type="category" stroke="#86868b" width={100} tick={{ fontSize: 12, fill: '#86868b' }} axisLine={false} tickLine={false} />
                <Tooltip 
                  contentStyle={chartTooltipStyle}
                  cursor={{ fill: 'rgba(0, 0, 0, 0.04)' }}
                />
                <Bar 
                  dataKey="score" 
                  fill={chartColors.rose} 
                  radius={[0, 6, 6, 0]} 
                  cursor="pointer"
                >
                  {barData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.regionId === activeRegion?.region_id ? '#2563eb' : chartColors.rose} 
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </motion.div>
      
      {/* Risk History Timeline */}
      <motion.div variants={itemVariants}>
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Risk Snapshot Timeline (Event-Driven Pipeline)</CardTitle>
          </CardHeader>
          <CardContent>
            <RiskSnapshotTimeline regionId={activeRegion?.region_id || 1} />
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  )
}
