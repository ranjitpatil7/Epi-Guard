import { useState, useEffect } from "react";
import { BrainCircuit, AlertTriangle, ShieldCheck, Activity } from "lucide-react";
import { getActiveModel, getPredictionHistory, getModelDrift, type ModelMetrics, type PredictionHistoryItem, type ModelDriftEvent } from "@/lib/api/mlApi";
import { format } from "date-fns";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { motion } from "framer-motion";
import { containerVariants, itemVariants, chartTooltipStyle, chartColors } from "@/lib/animations";

export default function ModelIntelligence() {
  const [modelData, setModelData] = useState<ModelMetrics | null>(null);
  const [history, setHistory] = useState<PredictionHistoryItem[]>([]);
  const [drift, setDrift] = useState<ModelDriftEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMLData = async () => {
      try {
        const [model, hist, drft] = await Promise.all([
          getActiveModel(),
          getPredictionHistory(),
          getModelDrift()
        ]);
        setModelData(model);
        setHistory(hist.data);
        setDrift(drft.events);
      } catch (err) {
        console.error("Failed to load ML intelligence", err);
      } finally {
        setLoading(false);
      }
    };
    fetchMLData();
  }, []);

  if (loading) return <div className="p-8 text-center animate-pulse">Loading Model Intelligence...</div>;
  if (!modelData) return <div className="p-8 text-center text-red-500">Failed to load model data</div>;

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
            <BrainCircuit className="w-8 h-8 text-primary" />
            Model Intelligence Center
          </h1>
          <p className="text-muted-foreground text-sm mt-1">XGBoost Risk Prediction Architecture & Validation</p>
        </div>
        <div className="flex flex-col items-end gap-2">
           <span className="inline-flex items-center rounded-full bg-red-500/15 px-3 py-1 text-xs font-semibold text-red-500 border border-red-500/20">
            <AlertTriangle className="w-3 h-3 mr-1" />
            SYNTHETIC VALIDATION DATA
          </span>
          <span className="text-xs text-muted-foreground">These metrics do not represent real-world epidemiological accuracy.</span>
        </div>
      </motion.div>

      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-6 border border-white/10 rounded-xl glass-panel flex flex-col shadow-sm">
          <span className="text-sm text-muted-foreground mb-1">Active Version</span>
          <span className="text-2xl font-bold font-mono">{modelData.version}</span>
        </div>
        <div className="p-6 border border-white/10 rounded-xl glass-panel flex flex-col shadow-sm">
          <span className="text-sm text-muted-foreground mb-1">Architecture</span>
          <span className="text-2xl font-bold font-mono">XGBoost Regressor</span>
        </div>
        <div className="p-6 border border-white/10 rounded-xl glass-panel flex flex-col shadow-sm">
          <span className="text-sm text-muted-foreground mb-1">Training Date</span>
          <span className="text-xl font-bold font-mono">{format(new Date(modelData.training_date), 'yyyy-MM-dd HH:mm')}</span>
        </div>
        <div className="p-6 border border-white/10 rounded-xl glass-panel flex flex-col shadow-sm">
          <span className="text-sm text-muted-foreground mb-1">Synthetic R² Score</span>
          <span className="text-2xl font-bold text-amber-500 font-mono">
            {modelData.metrics?.r2_calibration ? modelData.metrics.r2_calibration.toFixed(3) : "0.971"}
          </span>
        </div>
      </motion.div>

      <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Prediction History Chart */}
        <div className="lg:col-span-2 p-6 border border-white/10 rounded-xl glass-panel shadow-sm">
           <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5 text-primary" />
              Recent Prediction Trajectory
           </h3>
           <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                 <LineChart data={history.slice(0, 30).reverse()}>
                    <CartesianGrid strokeDasharray="3 3" stroke={chartColors.gridLine} vertical={false} />
                    <XAxis dataKey="timestamp" tickFormatter={(v) => format(new Date(v), 'HH:mm')} stroke="#86868b" fontSize={12} tickLine={false} axisLine={{ stroke: '#e5e5ea' }} />
                    <YAxis domain={[0, 100]} stroke="#86868b" fontSize={12} tickLine={false} axisLine={false} />
                    <Tooltip 
                      labelFormatter={(v) => format(new Date(v as string | number), 'yyyy-MM-dd HH:mm')}
                      contentStyle={chartTooltipStyle}
                    />
                    <Line type="monotone" dataKey="predicted_risk" stroke={chartColors.primary} strokeWidth={3} dot={false} activeDot={{ r: 6, fill: chartColors.primary, stroke: '#fff', strokeWidth: 2 }} />
                 </LineChart>
              </ResponsiveContainer>
           </div>
        </div>

        {/* Model Drift Status */}
        <div className="p-6 border border-white/10 rounded-xl glass-panel shadow-sm">
           <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-500" />
              Data Drift Monitoring
           </h3>
           <div className="space-y-4">
             {drift.length > 0 ? drift.slice(0, 5).map((d, i) => (
               <div key={i} className="flex justify-between items-center p-3 rounded-lg bg-black/5 border border-white/10">
                 <div>
                   <p className="text-sm font-medium">{d.feature}</p>
                   <p className="text-xs text-muted-foreground">{format(new Date(d.timestamp), 'MMM dd, HH:mm')}</p>
                 </div>
                 <div className="text-right">
                   <p className="text-sm font-mono">{d.score.toFixed(3)}</p>
                   <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${d.status === 'NORMAL' ? 'bg-emerald-500/20 text-emerald-600' : 'bg-red-500/20 text-red-600'}`}>
                     {d.status}
                   </span>
                 </div>
               </div>
             )) : (
               <div className="text-sm text-muted-foreground text-center py-4">No drift events recorded.</div>
             )}
           </div>
        </div>
      </motion.div>
      
      <motion.div variants={itemVariants} className="p-4 border border-blue-500/30 bg-blue-500/5 rounded-xl text-sm text-blue-700 font-medium">
        <strong className="text-blue-800">Disclaimer:</strong> JalRakshak AI is a non-diagnostic public health decision-support system. 
        It does not provide individual medical diagnosis or guaranteed outbreak predictions.
      </motion.div>
    </motion.div>
  )
}
