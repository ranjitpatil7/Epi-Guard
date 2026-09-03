import { useState, useEffect } from "react";
import { BellRing, ShieldAlert, CheckCircle2, AlertTriangle, Info } from "lucide-react";
import { getAlerts, acknowledgeAlert, type AlertItem } from "@/lib/api/alertsApi";
import { format } from "date-fns";
import { motion } from "framer-motion";
import { containerVariants, itemVariants } from "@/lib/animations";

export default function AlertsCenter() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      const data = await getAlerts(true);
      setAlerts(data.data);
    } catch (err) {
      console.error("Failed to load alerts", err);
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async (id: number) => {
    try {
      await acknowledgeAlert(id);
      // Optimistic update
      setAlerts(alerts.filter(a => a.id !== id));
    } catch (err) {
      console.error("Failed to acknowledge alert", err);
    }
  };

  if (loading) return <div className="p-8 text-center animate-pulse">Loading Alerts...</div>;

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
            <BellRing className="w-8 h-8 text-primary" />
            Active Alerts Command Center
          </h1>
          <p className="text-muted-foreground text-sm mt-1">Review and manage AI-generated early warnings</p>
        </div>
      </motion.div>

      <motion.div variants={itemVariants} className="space-y-4">
        {alerts.length === 0 ? (
           <div className="p-12 text-center text-emerald-600 border rounded-xl border-dashed border-emerald-500/30 bg-emerald-500/5">
             <CheckCircle2 className="w-12 h-12 mx-auto mb-4 opacity-50" />
             No active alerts. The system is operating normally.
           </div>
        ) : (
          alerts.map(a => (
            <motion.div variants={itemVariants} key={a.id} className="p-6 border border-white/10 rounded-xl glass-panel flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-lg hover:-translate-y-1 hover:shadow-xl transition-all duration-300">
              <div className="flex items-start gap-4">
                <div className={`p-4 rounded-full ${a.severity === 'CRITICAL' ? 'bg-red-500/10 text-red-600' : a.severity === 'HIGH' ? 'bg-amber-500/10 text-amber-600' : 'bg-blue-500/10 text-blue-600'}`}>
                  {a.severity === 'CRITICAL' ? <ShieldAlert className="w-8 h-8" /> : a.severity === 'HIGH' ? <AlertTriangle className="w-8 h-8" /> : <Info className="w-8 h-8" />}
                </div>
                <div>
                  <div className="flex items-center gap-3">
                    <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider ${a.severity === 'CRITICAL' ? 'bg-red-500 text-white' : a.severity === 'HIGH' ? 'bg-amber-500 text-white' : 'bg-blue-500 text-white'}`}>
                      {a.severity}
                    </span>
                    <span className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">Region {a.region_id}</span>
                    <span className="text-xs text-muted-foreground">• {format(new Date(a.created_at), 'MMM dd, yyyy HH:mm')}</span>
                  </div>
                  <h3 className="text-xl font-bold mt-2 text-foreground">{a.message}</h3>
                </div>
              </div>
              <div className="flex shrink-0">
                <motion.button 
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleAcknowledge(a.id)}
                  className="px-6 py-2.5 rounded-lg bg-primary text-primary-foreground font-bold hover:bg-primary/90 transition-all shadow-sm"
                >
                  Acknowledge & Resolve
                </motion.button>
              </div>
            </motion.div>
          ))
        )}
      </motion.div>
    </motion.div>
  );
}
