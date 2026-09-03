import { useParams, Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { getRegionDetail } from "@/lib/api/regionsApi"
import { getMLRisk } from "@/lib/api/riskApi"
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/spinner"
import { ArrowLeft, CloudRain, ShieldAlert, Users, TrendingUp, AlertTriangle, Zap, Activity } from "lucide-react"
import { motion } from "framer-motion"
import { containerVariants, itemVariants } from "@/lib/animations"

export default function RegionalDetail() {
  const { regionId } = useParams()
  
  const { data: region, isLoading: isRegionLoading } = useQuery({
    queryKey: ['region', regionId],
    queryFn: () => getRegionDetail(Number(regionId)),
    enabled: !!regionId
  })

  const { data: risk, isLoading: isRiskLoading } = useQuery({
    queryKey: ['mlRisk', regionId],
    queryFn: () => getMLRisk(Number(regionId)),
    enabled: !!regionId
  })

  if (isRegionLoading || isRiskLoading) {
    return <div className="flex h-full items-center justify-center"><Spinner size="lg" /></div>
  }

  if (!region || !risk) {
    return <div className="p-12 text-center text-destructive">Region or Risk Data not found.</div>
  }

  const getRiskBadge = (level: string) => {
    switch (level) {
      case 'CRITICAL': return <Badge variant="destructive">CRITICAL</Badge>;
      case 'HIGH': return <Badge className="bg-orange-500 hover:bg-orange-600">HIGH</Badge>;
      case 'MODERATE': return <Badge variant="warning">MODERATE</Badge>;
      case 'GUARDED': return <Badge className="bg-yellow-400 text-yellow-900 hover:bg-yellow-500">GUARDED</Badge>;
      default: return <Badge variant="success">LOW</Badge>;
    }
  }

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      <motion.div variants={itemVariants} className="flex items-center gap-4 border-b border-white/10 pb-4">
        <Link to="/regional-intelligence" className="p-2 hover:bg-black/5 rounded-full transition-colors">
          <ArrowLeft className="w-5 h-5 text-muted-foreground" />
        </Link>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{region.name}</h1>
          <p className="text-muted-foreground text-sm">
            {region.district ? `${region.district}, ` : ''}{region.state} • Population: {region.population.toLocaleString()}
          </p>
        </div>
      </motion.div>

      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-t-4 border-t-primary relative overflow-hidden glass-panel border-white/10 shadow-lg">
          <div className="absolute top-2 right-2 flex flex-col items-end opacity-20 pointer-events-none">
            <Zap className="w-12 h-12" />
          </div>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground flex justify-between">
              <span>ML Estimated Risk</span>
              <Badge variant="outline" className="text-xs">v{risk.model_version}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-end gap-3">
              <span className="text-5xl font-bold tracking-tighter">{risk?.estimated_risk_score.toFixed(1) || "N/A"}</span>
              <span className="mb-2">{risk && getRiskBadge(risk.risk_level)}</span>
            </div>
            
            <div className="mt-4 space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-muted-foreground flex items-center"><Activity className="w-3 h-3 mr-1"/> Confidence</span>
                <span className={risk.confidence_score > 80 ? "text-green-500" : risk.confidence_score > 50 ? "text-yellow-500" : "text-red-500"}>
                  {risk.confidence_score.toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-muted-foreground">Data Quality</span>
                <span>{risk.data_quality_score.toFixed(1)}%</span>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center">
              <TrendingUp className="w-4 h-4 mr-2 text-primary" /> Forecast (+7d)
            </CardTitle>
          </CardHeader>
          <CardContent>
             <div className="space-y-3 mt-2">
              {risk.forecasts?.map((f, i) => (
                 <div key={i} className="flex justify-between items-center border-b border-border/50 pb-2 last:border-0 last:pb-0">
                    <span className="text-sm text-muted-foreground">+{f.horizon}</span>
                    <div className="flex items-center gap-2">
                      <span className="font-bold">{f.prediction.toFixed(1)}</span>
                      {getRiskBadge(f.prediction >= 75 ? 'CRITICAL' : f.prediction >= 60 ? 'HIGH' : f.prediction >= 40 ? 'MODERATE' : f.prediction >= 20 ? 'GUARDED' : 'LOW')}
                    </div>
                 </div>
              ))}
             </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center">
              <CloudRain className="w-4 h-4 mr-2 text-blue-500" /> Rainfall (7d)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{risk?.features_used?.rainfall_7d?.toFixed(1) || 0} <span className="text-sm font-normal text-muted-foreground">mm</span></div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center">
              <ShieldAlert className="w-4 h-4 mr-2 text-destructive" /> Disease Cases (14d)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{risk?.features_used?.cases_14d || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center">
              <Users className="w-4 h-4 mr-2 text-primary" /> Community Reports
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{risk?.features_used?.reports_7d || 0}</div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-white/10 shadow-lg glass-panel">
            <CardHeader className="flex flex-row items-center justify-between border-b border-white/10 pb-4">
              <CardTitle>AI Explainability (SHAP)</CardTitle>
              {risk.is_synthetic_training_based && (
                <Badge variant="outline" className="text-xs text-amber-600 border-amber-500/30 bg-amber-500/10">Synthetic Data</Badge>
              )}
            </CardHeader>
            <CardContent className="pt-6">
              {risk?.contributing_factors && risk.contributing_factors.length > 0 ? (
                <div className="space-y-4">
                  {risk.contributing_factors.map((factor: any, i: number) => (
                    <div key={i} className="flex flex-col bg-white/5 border border-white/10 p-4 rounded-xl shadow-sm">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center">
                          {factor.direction === 'positive' ? 
                            <TrendingUp className="w-4 h-4 text-red-500 mr-2 shrink-0" /> :
                            <TrendingUp className="w-4 h-4 text-emerald-500 mr-2 shrink-0 rotate-180" />
                          }
                          <span className="text-sm font-semibold capitalize text-foreground">{factor.feature.replace(/_/g, ' ')}</span>
                        </div>
                        <Badge variant="outline" className={factor.direction === 'positive' ? "text-red-500 border-red-500/30 bg-red-50" : "text-emerald-600 border-emerald-500/30 bg-emerald-50"}>
                          {factor.direction === 'positive' ? '+' : ''}{factor.impact.toFixed(2)} pts
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground pl-6">{factor.explanation}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground text-sm">No elevated risk factors detected.</p>
              )}
            </CardContent>
            <CardFooter className="bg-black/5 pt-4 rounded-b-xl text-xs text-muted-foreground">
              <AlertTriangle className="w-3 h-3 mr-2 inline" /> This is a public health decision-support tool. It is not a clinical diagnosis.
            </CardFooter>
          </Card>
          
          <Card className="border-white/10 shadow-lg glass-panel">
            <CardHeader className="border-b border-white/10">
              <CardTitle>Recommended Actions</CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="p-8 text-center text-muted-foreground border border-dashed border-white/10 rounded-xl text-sm bg-white/5">
                AI Copilot recommendations will be displayed here in Phase 4.
              </div>
            </CardContent>
          </Card>
        </div>
        
        <div className="space-y-6">
          <Card className="border-white/10 shadow-lg glass-panel">
            <CardHeader className="border-b border-white/10">
              <CardTitle>Map Geometry</CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="h-48 bg-black/5 rounded-xl flex items-center justify-center text-muted-foreground text-xs font-medium border border-white/10">
                {region.geometry ? "GeoJSON Available" : "No Geometry Data"}
              </div>
            </CardContent>
          </Card>
        </div>
      </motion.div>
    </motion.div>
  )
}
