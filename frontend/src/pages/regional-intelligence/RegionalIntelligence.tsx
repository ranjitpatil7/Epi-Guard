import { useQuery } from "@tanstack/react-query"
import { getRegions } from "@/lib/api/regionsApi"
import { getCurrentRisk } from "@/lib/api/riskApi"
import { Spinner } from "@/components/ui/spinner"
import { Badge } from "@/components/ui/badge"
import { Search } from "lucide-react"
import { Input } from "@/components/ui/input"
import { useState } from "react"
import { Link } from "react-router-dom"
import { motion } from "framer-motion"
import { containerVariants, itemVariants } from "@/lib/animations"

export default function RegionalIntelligence() {
  const [searchTerm, setSearchTerm] = useState("")
  
  const { data: regions, isLoading: isLoadingRegions } = useQuery({
    queryKey: ['regions'],
    queryFn: getRegions
  })

  const { data: riskData, isLoading: isLoadingRisk } = useQuery({
    queryKey: ['currentRisk'],
    queryFn: getCurrentRisk
  })

  if (isLoadingRegions || isLoadingRisk) return <div className="flex h-full items-center justify-center"><Spinner size="lg" /></div>

  // Merge data
  const mergedData = regions?.map(region => {
    const risk = riskData?.find(r => r.region_id === region.id)
    return {
      ...region,
      risk_score: risk?.estimated_risk_score ?? risk?.risk_score ?? 0,
      risk_level: risk?.risk_level || 'UNKNOWN',
      factors: risk?.contributing_factors || [],
      updated_at: risk?.calculation_timestamp || new Date().toISOString()
    }
  }) || []
  
  const filteredData = mergedData.filter(item => 
    item.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    item.district?.toLowerCase().includes(searchTerm.toLowerCase())
  ).sort((a, b) => b.risk_score - a.risk_score)

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
      <motion.div variants={itemVariants} className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4 border-b border-white/10 pb-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Regional Intelligence</h1>
          <p className="text-muted-foreground text-sm">Detailed metrics and risk profiles for all monitored areas.</p>
        </div>
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search regions..."
            className="pl-9 glass-panel border-white/10 focus-visible:ring-primary"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </motion.div>

      <motion.div variants={itemVariants} className="border border-white/10 rounded-xl glass-panel shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-muted-foreground bg-black/5 border-b border-white/10 uppercase">
              <tr>
                <th className="px-6 py-4 font-medium">Region</th>
                <th className="px-6 py-4 font-medium">State / District</th>
                <th className="px-6 py-4 font-medium">Risk Level</th>
                <th className="px-6 py-4 font-medium">Risk Score</th>
                <th className="px-6 py-4 font-medium">Key Factor</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredData.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-muted-foreground">
                    No regions found matching your search.
                  </td>
                </tr>
              ) : (
                filteredData.map((item, _) => (
                  <motion.tr 
                    key={item.id} 
                    variants={itemVariants}
                    className="border-b border-white/10 hover:bg-black/5 transition-colors"
                  >
                    <td className="px-6 py-4 font-medium text-foreground">{item.name}</td>
                    <td className="px-6 py-4 text-muted-foreground">{item.state} / {item.district}</td>
                    <td className="px-6 py-4">{getRiskBadge(item.risk_level)}</td>
                    <td className="px-6 py-4 font-mono font-medium">{item.risk_score}</td>
                    <td className="px-6 py-4 text-muted-foreground truncate max-w-[200px]">
                      {typeof item.factors[0] === 'string' 
                        ? item.factors[0] 
                        : (item.factors[0]?.explanation || '-')}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link to={`/regional-intelligence/${item.id}`} className="text-primary hover:text-primary/80 font-medium text-sm hover:underline">
                        View Details →
                      </Link>
                    </td>
                  </motion.tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </motion.div>
    </motion.div>
  )
}
