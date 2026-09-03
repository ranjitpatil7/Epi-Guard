import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Spinner } from "@/components/ui/spinner"
import { BrainCircuit } from "lucide-react"
import { apiClient } from "@/lib/api/client"

interface ContributingFactor {
  feature: string
  value: number
  impact: number
  direction: "positive" | "negative"
  explanation: string
}

interface RiskExplanationPanelProps {
  riskScore: number
  riskLevel: string
  contributingFactors?: ContributingFactor[]
}

export function RiskExplanationPanel({ riskScore, riskLevel, contributingFactors = [] }: RiskExplanationPanelProps) {
  const [aiSummary, setAiSummary] = useState<string | null>(null)
  const [isLoadingAi, setIsLoadingAi] = useState(false)

  // Map backend feature names to readable labels
  const formatFeatureName = (name: string) => {
    return name
      .replace(/_7d|_14d|avg_/g, '')
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase())
  }

  // Calculate percentage of total absolute impact for the progress bars
  const totalImpact = contributingFactors.reduce((sum, factor) => sum + Math.abs(factor.impact), 0)
  
  const factorsWithPercentage = contributingFactors.map(factor => ({
    ...factor,
    percentage: totalImpact > 0 ? (Math.abs(factor.impact) / totalImpact) * 100 : 0,
    label: formatFeatureName(factor.feature)
  })).slice(0, 5) // Take top 5

  useEffect(() => {
    async function fetchAiSummary() {
      if (contributingFactors.length === 0) return
      
      setIsLoadingAi(true)
      try {
        const res = await apiClient.post("/copilot/explain-risk", {
          contributing_factors: contributingFactors 
        })
        setAiSummary(res.data.explanation)
      } catch (e) {
        console.error("Failed to fetch AI explanation", e)
      } finally {
        setIsLoadingAi(false)
      }
    }

    fetchAiSummary()
  }, [contributingFactors])

  if (!contributingFactors || contributingFactors.length === 0) {
    return null
  }

  return (
    <Card className="border-primary/20 bg-gradient-to-br from-background to-primary/5">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BrainCircuit className="h-5 w-5 text-primary" />
          Explainable AI (XAI)
        </CardTitle>
        <p className="text-sm text-muted-foreground mt-1.5">
          Why is this region's risk score <strong>{riskScore.toFixed(0)} ({riskLevel})</strong>?
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        
        {/* SHAP Progress Bars */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Main Contributing Factors</h4>
          {factorsWithPercentage.map((factor, idx) => (
            <div key={idx} className="space-y-1">
              <div className="flex justify-between text-sm">
                <span className="font-medium text-foreground">{factor.label}</span>
                <span className="text-muted-foreground">{factor.percentage.toFixed(0)}%</span>
              </div>
              <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                <div 
                  className={`h-full rounded-full ${factor.direction === 'positive' ? 'bg-rose-500' : 'bg-emerald-500'}`}
                  style={{ width: `${factor.percentage}%` }}
                />
              </div>
              <p className="text-xs text-muted-foreground pt-1">{factor.explanation}</p>
            </div>
          ))}
        </div>

        {/* AI Copilot Summary */}
        <div className="mt-6 rounded-lg border border-primary/20 bg-primary/10 p-4 relative overflow-hidden glass-panel">
          <div className="absolute top-0 left-0 w-1 h-full bg-primary" />
          <h4 className="text-xs font-semibold text-primary uppercase tracking-wider mb-2 flex items-center gap-2">
            AI Copilot Summary
          </h4>
          {isLoadingAi ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Spinner size="sm" /> Generating explanation...
            </div>
          ) : (
            <p className="text-sm text-foreground leading-relaxed">
              {aiSummary || "The model indicates elevated risk based on these top indicators."}
            </p>
          )}
        </div>

      </CardContent>
    </Card>
  )
}
