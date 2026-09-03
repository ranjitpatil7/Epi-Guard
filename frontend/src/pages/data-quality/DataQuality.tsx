import { useState, useEffect } from "react";
import { Database, Server, HardDrive, CheckCircle2, AlertTriangle, ShieldCheck } from "lucide-react";
import { getDataQuality, type DataQualityMetrics } from "@/lib/api/dataQualityApi";
import { motion } from "framer-motion";
import { containerVariants, itemVariants } from "@/lib/animations";

export default function DataQuality() {
  const [metrics, setMetrics] = useState<DataQualityMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchQuality = async () => {
      try {
        const data = await getDataQuality();
        setMetrics(data);
      } catch (err) {
        console.error("Failed to load data quality metrics", err);
      } finally {
        setLoading(false);
      }
    };
    fetchQuality();
  }, []);

  if (loading) return <div className="p-8 text-center animate-pulse">Loading Data Quality...</div>;
  if (!metrics) return <div className="p-8 text-center text-red-500">Failed to load metrics</div>;

  const MetricCard = ({ label, value, icon: Icon }: any) => (
    <motion.div variants={itemVariants} className="p-6 border border-white/10 rounded-2xl glass-panel flex flex-col items-center justify-center relative overflow-hidden group shadow-lg hover:-translate-y-1 hover:shadow-xl transition-all duration-300">
      <Icon className="w-20 h-20 absolute -right-4 -bottom-4 text-primary/5 group-hover:text-primary/10 transition-colors" />
      <span className="text-sm font-medium text-muted-foreground mb-2 z-10">{label}</span>
      <div className="flex items-baseline gap-1 z-10">
        <span className="text-4xl font-bold tracking-tighter font-mono">{value.toFixed(1)}</span>
        <span className="text-xl font-medium text-muted-foreground">%</span>
      </div>
    </motion.div>
  );

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      <motion.div variants={itemVariants} className="flex justify-between items-end border-b border-white/10 pb-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Database className="w-8 h-8 text-primary" />
            Data Quality Center
          </h1>
          <p className="text-muted-foreground text-sm mt-1">Monitor ingestion pipelines, missing data, and freshness</p>
        </div>
        <div className="max-w-xs text-right">
           <div className="inline-flex items-center gap-2 text-xs text-amber-600 bg-amber-500/10 px-3 py-1.5 rounded-full border border-amber-500/20 shadow-sm font-medium">
             <AlertTriangle className="w-4 h-4 shrink-0" />
             Lower data quality reduces ML model confidence
           </div>
        </div>
      </motion.div>

      <motion.div variants={itemVariants} className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <MetricCard label="Overall Score" value={metrics.overall_quality} icon={ShieldCheck} />
        <MetricCard label="Completeness" value={metrics.completeness} icon={Database} />
        <MetricCard label="Freshness" value={metrics.freshness} icon={Server} />
        <MetricCard label="Validity" value={metrics.validity} icon={CheckCircle2} />
        <MetricCard label="Coverage" value={metrics.coverage} icon={HardDrive} />
      </motion.div>

      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
        <div className="p-6 border border-white/10 rounded-2xl glass-panel shadow-lg">
          <h3 className="text-lg font-bold mb-4">Pipeline Status</h3>
          <div className="space-y-4">
            {metrics.sources.map(src => (
              <div key={src.name} className="flex justify-between items-center p-3 bg-black/5 rounded-xl border border-white/10 shadow-sm">
                <span className="font-medium text-foreground">{src.name}</span>
                <div className="flex items-center gap-4">
                  <span className="font-mono text-sm font-medium">{src.quality.toFixed(1)}% Q-Score</span>
                  <span className={`px-2 py-0.5 rounded-md text-xs font-bold shadow-sm border ${src.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20' : 'bg-red-500/10 text-red-600 border-red-500/20'}`}>
                    {src.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="p-6 border border-white/10 rounded-2xl glass-panel shadow-lg">
          <h3 className="text-lg font-bold mb-4">Quality Confidence Impact</h3>
          <p className="text-sm text-muted-foreground leading-relaxed">
            The XGBoost Regional Risk Model dynamically computes a Confidence Interval for every prediction. 
            If the Data Quality drops due to missing features or stale pipeline data, the RiskFusionService penalizes the Confidence Score.
          </p>
          <div className="mt-6 flex items-center justify-between p-5 bg-black/5 rounded-xl border border-white/10 shadow-inner">
             <span className="text-sm font-semibold">Current Penalty</span>
             <span className="font-mono font-bold text-xl text-amber-600">-{(100 - metrics.overall_quality).toFixed(1)}%</span>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
