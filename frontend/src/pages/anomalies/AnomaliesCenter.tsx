import { useState, useEffect } from "react";
import { Activity, AlertTriangle, ShieldAlert } from "lucide-react";
import { motion } from "framer-motion";
import { containerVariants, itemVariants } from "@/lib/animations";
import { getAnomalies, type AnomalyItem } from "@/lib/api/anomaliesApi";
import { format } from "date-fns";

export default function AnomaliesCenter() {
  const [anomalies, setAnomalies] = useState<AnomalyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterSeverity, setFilterSeverity] = useState<string>("ALL");

  useEffect(() => {
    const fetchAnomalies = async () => {
      try {
        const data = await getAnomalies();
        setAnomalies(data.data);
      } catch (err) {
        console.error("Failed to load anomalies", err);
      } finally {
        setLoading(false);
      }
    };
    fetchAnomalies();
  }, []);

  if (loading) return <div className="p-8 text-center animate-pulse">Loading Anomalies...</div>;

  const filtered = filterSeverity === "ALL" ? anomalies : anomalies.filter(a => a.severity === filterSeverity);

  const stats = {
    total: anomalies.length,
    critical: anomalies.filter(a => a.severity === 'CRITICAL').length,
    high: anomalies.filter(a => a.severity === 'HIGH').length,
    moderate: anomalies.filter(a => a.severity === 'MODERATE').length,
  };

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
            <Activity className="w-8 h-8 text-primary" />
            Advanced Anomaly Center
          </h1>
          <p className="text-muted-foreground text-sm mt-1">Multi-factor detection via Z-Score, IQR, and Isolation Forest</p>
        </div>
      </motion.div>

      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-6 border border-white/10 rounded-xl glass-panel flex flex-col shadow-lg">
          <span className="text-sm text-muted-foreground mb-1">Total Detected</span>
          <span className="text-3xl font-bold">{stats.total}</span>
        </div>
        <div className="p-6 border border-white/10 rounded-xl bg-red-50 flex flex-col shadow-sm">
          <span className="text-sm text-red-500 font-medium mb-1">Critical Anomalies</span>
          <span className="text-3xl font-bold text-red-600">{stats.critical}</span>
        </div>
        <div className="p-6 border border-white/10 rounded-xl bg-amber-50 flex flex-col shadow-sm">
          <span className="text-sm text-amber-600 font-medium mb-1">High Anomalies</span>
          <span className="text-3xl font-bold text-amber-600">{stats.high}</span>
        </div>
        <div className="p-6 border border-white/10 rounded-xl bg-blue-50 flex flex-col shadow-sm">
          <span className="text-sm text-blue-600 font-medium mb-1">Moderate</span>
          <span className="text-3xl font-bold text-blue-600">{stats.moderate}</span>
        </div>
      </motion.div>

      <motion.div variants={itemVariants} className="flex gap-2">
        {["ALL", "CRITICAL", "HIGH", "MODERATE"].map(s => (
          <motion.button 
            key={s} 
            whileTap={{ scale: 0.95 }}
            onClick={() => setFilterSeverity(s)}
            className={`px-4 py-1.5 rounded-full text-sm font-semibold transition-colors shadow-sm ${filterSeverity === s ? 'bg-primary text-primary-foreground' : 'bg-white/5 border border-white/10 text-muted-foreground hover:bg-white/10'}`}
          >
            {s}
          </motion.button>
        ))}
      </motion.div>

      <motion.div variants={itemVariants} className="space-y-4">
        {filtered.length === 0 ? (
           <div className="p-12 text-center text-muted-foreground border rounded-xl border-dashed bg-white/5">
             No anomalies found matching criteria.
           </div>
        ) : (
          filtered.map(a => (
            <motion.div variants={itemVariants} key={a.id} className="p-5 border border-white/10 rounded-xl glass-panel flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-lg hover:-translate-y-1 hover:shadow-xl transition-all duration-300">
              <div className="flex items-start gap-4">
                <div className={`p-3 rounded-lg ${a.severity === 'CRITICAL' ? 'bg-red-500/10 text-red-600' : a.severity === 'HIGH' ? 'bg-amber-500/10 text-amber-600' : 'bg-blue-500/10 text-blue-600'}`}>
                  {a.severity === 'CRITICAL' ? <ShieldAlert className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-bold text-foreground">{a.feature} Anomaly</h3>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-black/5 uppercase tracking-wide">Region {a.region_id}</span>
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">{a.explanation}</p>
                  <div className="flex items-center gap-4 mt-2 text-xs font-mono text-muted-foreground bg-black/5 px-3 py-1.5 rounded-md inline-flex">
                    <span>Observed: {a.observed_value.toFixed(2)}</span>
                    <span>Expected: {a.expected_mean.toFixed(2)}</span>
                    <span>Z-Score: {a.z_score.toFixed(2)}</span>
                  </div>
                </div>
              </div>
              <div className="text-right flex flex-col items-end">
                <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider ${a.severity === 'CRITICAL' ? 'bg-red-500 text-white shadow-sm' : a.severity === 'HIGH' ? 'bg-amber-500 text-white shadow-sm' : 'bg-blue-500 text-white shadow-sm'}`}>
                  {a.severity}
                </span>
                <span className="text-xs font-medium text-muted-foreground mt-2">{format(new Date(a.timestamp), 'MMM dd, yyyy HH:mm')}</span>
              </div>
            </motion.div>
          ))
        )}
      </motion.div>
    </motion.div>
  );
}
