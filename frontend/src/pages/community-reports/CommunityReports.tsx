import { useState, useEffect } from "react";
import { MessageSquare, User, MapPin } from "lucide-react";
import { getCommunityReports, type CommunityReportItem } from "@/lib/api/communityReportsApi";
import { format } from "date-fns";
import { motion } from "framer-motion";
import { containerVariants, itemVariants } from "@/lib/animations";

export default function CommunityReports() {
  const [reports, setReports] = useState<CommunityReportItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const data = await getCommunityReports();
        setReports(data.data);
      } catch (err) {
        console.error("Failed to load community reports", err);
      } finally {
        setLoading(false);
      }
    };
    fetchReports();
  }, []);

  if (loading) return <div className="p-8 text-center animate-pulse">Loading Community Reports...</div>;

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
            <MessageSquare className="w-8 h-8 text-primary" />
            Community Report Intelligence
          </h1>
          <p className="text-muted-foreground text-sm mt-1">NLP-processed field signals and community observations</p>
        </div>
        <div className="flex flex-col items-end gap-2">
           <span className="inline-flex items-center rounded-full bg-blue-500/15 px-3 py-1 text-xs font-semibold text-blue-600 border border-blue-500/20 uppercase tracking-widest shadow-sm">
            COMMUNITY-REPORTED INFORMATION
          </span>
          <span className="text-xs text-muted-foreground">Not medically verified epidemiological data.</span>
        </div>
      </motion.div>

      <motion.div variants={itemVariants} className="space-y-4">
        {reports.length === 0 ? (
           <div className="p-12 text-center text-muted-foreground border rounded-xl border-dashed bg-white/5">
             No community reports available.
           </div>
        ) : (
          reports.map(r => (
            <motion.div variants={itemVariants} key={r.id} className="p-6 border border-white/10 rounded-xl glass-panel flex flex-col md:flex-row gap-6 shadow-lg hover:-translate-y-1 hover:shadow-xl transition-all duration-300">
              <div className="flex-1 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <User className="w-4 h-4" /> Anonymous Reporter
                    <span className="text-muted-foreground/50">|</span>
                    <MapPin className="w-4 h-4" /> Region Unspecified
                  </div>
                  <span className="text-xs text-muted-foreground font-mono bg-black/5 px-2 py-1 rounded">
                    {format(new Date(r.created_at), 'yyyy-MM-dd HH:mm')}
                  </span>
                </div>
                
                <p className="text-lg italic border-l-4 border-primary/30 pl-4 py-1 text-foreground">
                  "{r.text}"
                </p>
                
                <div className="flex flex-wrap gap-2 pt-2">
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-white/10 border border-white/10 shadow-sm text-foreground">
                    NLP Severity: {r.nlp_severity.toFixed(2)}
                  </span>
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-white/10 border border-white/10 shadow-sm text-foreground">
                    Status: {r.status}
                  </span>
                  
                  {/* Extracted NLP Signals Based on Severity/Keywords - Simple Heuristic for UI */}
                  {r.text.toLowerCase().includes('water') && (
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-500/10 text-blue-600 border border-blue-500/30">
                      Water Contamination Signal
                    </span>
                  )}
                  {(r.text.toLowerCase().includes('sick') || r.text.toLowerCase().includes('fever') || r.text.toLowerCase().includes('pain')) ? (
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-red-500/10 text-red-600 border border-red-500/30">
                      Disease Signal
                    </span>
                  ): null}
                </div>
              </div>
              <div className="shrink-0 flex items-center justify-center w-32 border-l border-white/10 pl-6">
                <div className="text-center">
                   <div className={`text-3xl font-black ${r.nlp_severity > 0.7 ? 'text-red-500' : r.nlp_severity > 0.4 ? 'text-amber-500' : 'text-emerald-500'}`}>
                     {(r.nlp_severity * 100).toFixed(0)}%
                   </div>
                   <div className="text-[10px] text-muted-foreground font-bold uppercase tracking-widest mt-1">Risk Weight</div>
                </div>
              </div>
            </motion.div>
          ))
        )}
      </motion.div>
    </motion.div>
  );
}
