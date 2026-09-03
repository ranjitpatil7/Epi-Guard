import { useState, useEffect } from 'react';
import { getAuditLogs, type AuditLogItem } from '@/lib/api/auditApi';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { format } from "date-fns";
import { Spinner } from "@/components/ui/spinner";
import { ShieldCheck, History } from "lucide-react";
import { motion } from "framer-motion";
import { containerVariants, itemVariants } from "@/lib/animations";

export default function AuditLog() {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await getAuditLogs(50);
        setLogs(response.data);
      } catch (error) {
        console.error("Failed to load audit logs", error);
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-20 space-y-4">
        <Spinner size="lg" />
        <p className="text-muted-foreground animate-pulse">Retrieving secure audit trails...</p>
      </div>
    );
  }

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6 max-w-6xl mx-auto"
    >
      <motion.div variants={itemVariants} className="flex justify-between items-end border-b border-white/10 pb-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <History className="w-8 h-8 text-primary" />
            System Audit Log
          </h1>
          <p className="text-muted-foreground text-sm mt-1">Immutable historical record of system activities and user actions.</p>
        </div>
      </motion.div>

      <motion.div variants={itemVariants} className="rounded-2xl border border-white/10 glass-panel shadow-lg overflow-hidden">
        <Table>
          <TableHeader className="bg-black/5">
            <TableRow className="border-white/10 hover:bg-transparent">
              <TableHead className="w-[180px] font-semibold">Timestamp</TableHead>
              <TableHead className="w-[100px] font-semibold">User ID</TableHead>
              <TableHead className="w-[140px] font-semibold">IP Address</TableHead>
              <TableHead className="font-semibold">Action Details</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {logs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="h-24 text-center text-muted-foreground">
                  No audit logs found.
                </TableCell>
              </TableRow>
            ) : (
              logs.map((log) => (
                <TableRow key={log.id} className="group hover:bg-black/5 border-white/10 transition-colors">
                  <TableCell className="font-medium text-xs whitespace-nowrap text-foreground/80">
                    {format(new Date(log.timestamp), "MMM dd, yyyy HH:mm:ss")}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2 font-medium">
                      <ShieldCheck className="w-4 h-4 text-emerald-600" />
                      {log.user_id}
                    </div>
                  </TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {log.ip_address}
                  </TableCell>
                  <TableCell className="text-sm text-foreground/90 font-medium">
                    {log.action}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </motion.div>
    </motion.div>
  )
}
