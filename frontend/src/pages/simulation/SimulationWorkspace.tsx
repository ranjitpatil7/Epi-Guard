import { useState } from "react"
import { useQuery, useMutation } from "@tanstack/react-query"
import { getRegions } from "@/lib/api/regionsApi"
import { getCurrentRisk, simulateWhatIf } from "@/lib/api/riskApi"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { Badge } from "@/components/ui/badge"
import { BrainCircuit, Play, Beaker } from "lucide-react"
import { motion } from "framer-motion"
import { containerVariants, itemVariants } from "@/lib/animations"

export default function SimulationWorkspace() {
  const [selectedRegionId, setSelectedRegionId] = useState<number | "">("")
  const [rainfallChange, setRainfallChange] = useState<number>(0)
  const [diseaseChange, setDiseaseChange] = useState<number>(0)
  const [simulationResult, setSimulationResult] = useState<any>(null)

  const { data: regions, isLoading: isLoadingRegions } = useQuery({
    queryKey: ['regions'],
    queryFn: getRegions
  })

  const { data: riskData, isLoading: isLoadingRisk } = useQuery({
    queryKey: ['currentRisk'],
    queryFn: getCurrentRisk
  })

  const simulateMutation = useMutation({
    mutationFn: async () => {
      if (!selectedRegionId) return null
      return await simulateWhatIf(Number(selectedRegionId), {
        rainfall: rainfallChange,
        cases_7d: diseaseChange
      })
    },
    onSuccess: (data) => {
      setSimulationResult(data)
    }
  })

  if (isLoadingRegions || isLoadingRisk) {
    return <div className="flex h-full items-center justify-center"><Spinner size="lg" /></div>
  }

  const baselineRisk = selectedRegionId ? riskData?.find(r => r.region_id === Number(selectedRegionId)) : null

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      <motion.div variants={itemVariants} className="flex justify-between items-end border-b border-white/10 pb-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center">
            <BrainCircuit className="w-8 h-8 mr-3 text-primary" />
            What-If Simulator
          </h1>
          <p className="text-muted-foreground text-sm">Test hypothetical environmental and health scenarios.</p>
        </div>
        <span className="inline-flex items-center rounded-full bg-amber-500/15 px-2.5 py-0.5 text-xs font-semibold text-amber-600 border border-amber-500/20 uppercase tracking-widest shadow-sm">
          HYPOTHETICAL SCENARIO
        </span>
      </motion.div>

      <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls */}
        <Card className="lg:col-span-1 border-white/10 shadow-lg glass-panel">
          <CardHeader>
            <CardTitle className="flex items-center text-base">
              <Beaker className="w-4 h-4 mr-2" />
              Scenario Parameters
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <label className="text-sm font-medium">Select Region</label>
              <select 
                className="w-full flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={selectedRegionId}
                onChange={(e) => setSelectedRegionId(e.target.value ? Number(e.target.value) : "")}
              >
                <option value="">-- Choose Region --</option>
                {regions?.map(r => (
                  <option key={r.id} value={r.id}>{r.name}</option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium flex justify-between">
                <span>Rainfall Override (mm)</span>
                <span className="text-muted-foreground">{rainfallChange > 0 ? `+${rainfallChange}` : rainfallChange}</span>
              </label>
              <input 
                type="range" min="-100" max="500" step="10" 
                value={rainfallChange} 
                onChange={(e) => setRainfallChange(Number(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>-100</span><span>0</span><span>+500</span>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium flex justify-between">
                <span>Disease Cases Override</span>
                <span className="text-muted-foreground">{diseaseChange > 0 ? `+${diseaseChange}` : diseaseChange}</span>
              </label>
              <input 
                type="range" min="-50" max="200" step="5" 
                value={diseaseChange} 
                onChange={(e) => setDiseaseChange(Number(e.target.value))}
                className="w-full"
              />
            </div>

            <Button 
              className="w-full" 
              disabled={!selectedRegionId || simulateMutation.isPending}
              onClick={() => simulateMutation.mutate()}
            >
              {simulateMutation.isPending ? <Spinner size="sm" className="mr-2" /> : <Play className="w-4 h-4 mr-2" />}
              Run Simulation
            </Button>
          </CardContent>
        </Card>

        {/* Results */}
        <div className="lg:col-span-2 space-y-6">
          {!selectedRegionId ? (
            <Card className="h-full flex items-center justify-center border-dashed border-white/10 bg-white/5">
              <p className="text-muted-foreground font-medium">Select a region and parameters to run a scenario.</p>
            </Card>
          ) : (
            <>
              <div className="grid grid-cols-2 gap-4">
                <Card className="border-white/10 shadow-lg glass-panel">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm text-muted-foreground">Baseline Risk (Current)</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-4xl font-bold">{(baselineRisk?.estimated_risk_score ?? baselineRisk?.risk_score ?? 0).toFixed(1)}</div>
                    <Badge variant="outline" className="mt-2 bg-white/5">{baselineRisk?.risk_level || "UNKNOWN"}</Badge>
                  </CardContent>
                </Card>
                <Card className={simulationResult ? "border-primary shadow-[0_8px_32px_rgba(59,130,246,0.1)] glass-panel" : "border-white/10 shadow-lg glass-panel"}>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm text-primary font-bold">Scenario Risk</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {simulationResult ? (
                      <>
                        <div className="flex items-end gap-3">
                          <div className="text-4xl font-bold">{simulationResult.what_if_risk_score.toFixed(1)}</div>
                          <div className={`text-sm mb-1 font-bold ${
                            simulationResult.what_if_risk_score > (baselineRisk?.estimated_risk_score || 0) 
                              ? "text-destructive" : "text-emerald-500"
                          }`}>
                            {simulationResult.what_if_risk_score > (baselineRisk?.estimated_risk_score || 0) ? "+" : ""}
                            {(simulationResult.what_if_risk_score - (baselineRisk?.estimated_risk_score || 0)).toFixed(1)}
                          </div>
                        </div>
                        <Badge variant="default" className="mt-2">{simulationResult.what_if_risk_level}</Badge>
                      </>
                    ) : (
                      <div className="text-muted-foreground text-sm flex h-12 items-center">Run simulation to view results.</div>
                    )}
                  </CardContent>
                </Card>
              </div>
              
              {simulationResult && (
                <Card className="border-white/10 shadow-lg glass-panel">
                  <CardHeader className="border-b border-white/10">
                    <CardTitle className="text-base">Scenario Contributors</CardTitle>
                  </CardHeader>
                  <CardContent className="pt-6">
                    <ul className="space-y-3 text-sm">
                      {simulationResult.what_if_factors.map((factor: any, i: number) => (
                        <li key={i} className="flex items-start bg-black/5 p-3 rounded-lg">
                          <span className={`mr-2 ${factor.direction === 'positive' ? 'text-destructive' : 'text-emerald-500'}`}>•</span>
                          <span className="text-muted-foreground">
                            <span className="font-semibold text-foreground">{factor.feature}</span>: {factor.explanation} 
                            <span className="ml-1 opacity-70 font-mono text-[10px] bg-white/5 px-1.5 py-0.5 rounded">
                              (Impact: {factor.impact > 0 ? '+' : ''}{factor.impact.toFixed(1)})
                            </span>
                          </span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      </motion.div>
    </motion.div>
  )
}
