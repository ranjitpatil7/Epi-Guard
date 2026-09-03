import { useState, useRef, useEffect } from "react"
import { Bot, User, Send, Sparkles, ShieldAlert, AlertTriangle, Loader2, Database, Brain, FileText, CheckCircle2, XCircle, Activity } from "lucide-react"
import { investigateWithCopilot, type CopilotResponse } from "@/lib/api/copilotApi"
import { useCopilotStreamStore } from "@/store/copilotStreamStore"
import { cn } from "@/lib/utils"
import { motion, AnimatePresence } from "framer-motion"
import { containerVariants, itemVariants } from "@/lib/animations"

export default function Copilot() {
  const [messages, setMessages] = useState<{role: string, content: string, response?: CopilotResponse}[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const { steps, isStreaming, startStream, endStream, failStream } = useCopilotStreamStore()
  
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (text: string = input) => {
    if (!text.trim()) return
    
    const userMsg = { role: "user", content: text }
    setMessages(prev => [...prev, userMsg])
    setInput("")
    setLoading(true)
    
    const reqId = crypto.randomUUID()
    startStream(reqId)
    
    try {
      // NOTE: We cast any as type matching CopilotRequest which now accepts request_id
      const resp = await investigateWithCopilot({ message: text, request_id: reqId } as any)
      setMessages(prev => [...prev, { role: "model", content: resp.answer, response: resp }])
      endStream()
    } catch (err: any) {
      const errMsg = err.response?.data?.detail || "Failed to connect to AI Copilot."
      setMessages(prev => [...prev, { role: "system", content: errMsg }])
      failStream(errMsg)
    } finally {
      setLoading(false)
    }
  }

  const renderAgentTrace = (trace: any[]) => {
    if (!trace || trace.length === 0) return null;
    return (
      <div className="mt-4 p-3 bg-card border rounded-md text-xs font-mono space-y-2">
        <div className="text-muted-foreground mb-2 flex items-center font-bold">
          <Brain className="w-3 h-3 mr-1" /> Agentic Investigation Trace
        </div>
        {trace.map((step, idx) => (
          <div key={idx} className="flex items-start space-x-2 border-l-2 border-primary/20 pl-2">
            <div className="text-muted-foreground min-w-[20px]">{step.iteration || '-'}</div>
            <div className="flex-1">
              {step.action === "final_synthesis" ? (
                <div className="text-primary font-bold">Synthesis Complete</div>
              ) : step.error ? (
                <div className="text-destructive flex items-center"><XCircle className="w-3 h-3 mr-1" /> {step.error}</div>
              ) : (
                <div className="flex flex-col">
                  <div className="flex items-center">
                    {step.success ? <CheckCircle2 className="w-3 h-3 mr-1 text-green-500" /> : <XCircle className="w-3 h-3 mr-1 text-destructive" />}
                    <span className="font-semibold text-primary/80">{step.tool}</span>
                    <span className="text-muted-foreground ml-2">({step.latency_ms}ms)</span>
                  </div>
                  <div className="text-muted-foreground mt-0.5 truncate max-w-[250px]">
                    Args: {JSON.stringify(step.arguments)}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="flex flex-col h-[calc(100vh-8rem)]"
    >
      <motion.div variants={itemVariants} className="mb-4">
        <h1 className="text-3xl font-bold tracking-tight flex items-center">
          <Bot className="w-8 h-8 mr-3 text-primary" />
          AI Copilot
        </h1>
        <p className="text-muted-foreground text-sm">Autonomous Intelligence Orchestrator</p>
      </motion.div>

      <motion.div variants={itemVariants} className="flex-1 flex flex-col border border-white/10 rounded-xl glass-panel shadow-lg relative overflow-hidden">
        
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          <AnimatePresence>
            {messages.length === 0 && (
              <motion.div 
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="flex flex-col items-center justify-center h-full text-center text-muted-foreground p-8"
              >
              <Bot className="w-16 h-16 text-primary mb-6" />
              <h2 className="text-xl font-semibold text-foreground mb-2">Initiate Investigation</h2>
              <p className="max-w-md mb-8">
                I can autonomously query spatial data, retrieve RAG evidence, run What-If simulations, and synthesize public health insights.
              </p>
              
              <div className="w-full max-w-2xl grid grid-cols-1 md:grid-cols-2 gap-3">
                {[
                  "Which regions currently have the highest estimated risk?",
                  "Why is Assam risk elevated?",
                  "Compare Assam and Meghalaya.",
                  "Summarize current alerts.",
                  "Show recent anomalies.",
                  "What if rainfall increases by 50mm in Assam?"
                ].map((prompt, i) => (
                  <button 
                    key={i} 
                    onClick={() => handleSend(prompt)}
                    className="text-left p-3 rounded-md bg-secondary/50 border hover:bg-secondary transition-colors text-sm text-foreground/80 flex items-start"
                  >
                    <Sparkles className="w-4 h-4 mr-2 mt-0.5 text-primary shrink-0" />
                    {prompt}
                  </button>
                ))}
              </div>
            </motion.div>
          )}

            {messages.map((msg, idx) => (
              <motion.div 
                layout
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                key={idx} 
                className={cn("flex w-full", msg.role === "user" ? "justify-end" : "justify-start")}
              >
                <div className={cn(
                  "flex max-w-[85%] rounded-2xl p-4 shadow-sm",
                  msg.role === "user" ? "bg-primary text-primary-foreground" : 
                  msg.role === "system" ? "bg-red-50 border border-red-100 text-red-600" :
                  "bg-white/5 border border-white/10 shadow-[0_4px_20px_rgba(0,0,0,0.03)]"
                )}>
                  {msg.role !== "user" && (
                    <div className="mr-4 shrink-0">
                      {msg.role === "system" ? <AlertTriangle className="w-6 h-6 text-red-600" /> : <Bot className="w-6 h-6 text-primary" />}
                    </div>
                  )}
                  
                  <div className="flex flex-col gap-3 overflow-hidden w-full">
                    <div className="text-sm whitespace-pre-wrap leading-relaxed">
                      {msg.content}
                    </div>
                    
                    {/* Structured Content Rendering */}
                    {msg.response && (
                      <div className="mt-4 space-y-4">
                        
                        {/* KPI Row */}
                        <div className="grid grid-cols-2 gap-2">
                          {msg.response.risk_level && (
                            <div className="bg-black/5 p-2 rounded-lg border border-white/10 text-xs flex justify-between items-center">
                              <span className="text-muted-foreground font-medium">Risk Level</span>
                              <span className={cn("font-bold", 
                                msg.response.risk_level === "CRITICAL" ? "text-red-600" :
                                msg.response.risk_level === "HIGH" ? "text-amber-600" :
                                msg.response.risk_level === "MODERATE" ? "text-amber-500" : "text-emerald-600"
                              )}>
                                {msg.response.risk_level}
                              </span>
                            </div>
                          )}
                          {msg.response.confidence !== undefined && (
                            <div className="bg-black/5 p-2 rounded-lg border border-white/10 text-xs flex justify-between items-center">
                              <span className="text-muted-foreground font-medium">Confidence</span>
                              <span className="font-bold text-foreground">{Math.round(msg.response.confidence * 100)}%</span>
                            </div>
                          )}
                        </div>

                        {/* Evidence RAG */}
                        {msg.response.retrieved_evidence && msg.response.retrieved_evidence.length > 0 && (
                          <div className="space-y-2 mt-4 border-t border-white/10 pt-4">
                            <h4 className="text-xs font-semibold text-muted-foreground uppercase flex items-center">
                              <FileText className="w-3 h-3 mr-1" /> Knowledge Graph Evidence
                            </h4>
                            {msg.response.retrieved_evidence.map((ev, i) => (
                              <div key={i} className="bg-white/5 border border-white/10 rounded-lg p-2 text-xs text-muted-foreground">
                                <span className="font-bold text-foreground block mb-1">Source: {ev.source}</span>
                                <span className="italic">"{ev.excerpt}"</span>
                              </div>
                            ))}
                          </div>
                        )}
                      
                      {/* Scenario Results */}
                      {msg.response.scenario_results && (
                        <div className="space-y-2 mt-4 border-t border-white/10 pt-4">
                           <h4 className="text-xs font-semibold text-muted-foreground uppercase flex items-center">
                            <Database className="w-3 h-3 mr-1" /> Scenario Analysis
                          </h4>
                          <pre className="text-xs p-3 bg-black/5 rounded-lg overflow-x-auto text-foreground font-mono">
                            {JSON.stringify(msg.response.scenario_results, null, 2)}
                          </pre>
                        </div>
                      )}

                      {/* Trace */}
                      {msg.response.agent_trace && renderAgentTrace(msg.response.agent_trace)}

                      <div className="border-t border-white/10 pt-3 mt-4 flex flex-col gap-1 text-[10px] text-muted-foreground">
                        <div className="flex items-center text-amber-600 uppercase font-bold tracking-wider">
                          <ShieldAlert className="w-3 h-3 mr-1" />
                          {msg.response.disclaimer}
                        </div>
                      </div>

                    </div>
                  )}
                </div>
                
                {msg.role === "user" && (
                  <div className="ml-4 shrink-0 flex items-end">
                    <User className="w-6 h-6 text-white" />
                  </div>
                )}
              </div>
            </motion.div>
          ))}
          </AnimatePresence>
          
          {loading && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex w-full justify-start"
            >
              <div className="flex flex-col bg-white/5 border border-white/10 rounded-2xl p-4 max-w-[80%] shadow-[0_4px_20px_rgba(0,0,0,0.03)]">
                
                {isStreaming && steps.length > 0 ? (
                  <div className="space-y-3 font-mono text-xs">
                    <div className="flex items-center text-primary font-bold mb-3 border-b border-white/10 pb-2">
                      <Activity className="w-4 h-4 mr-2 animate-pulse" />
                      Live Execution Timeline
                    </div>
                    {steps.map((step, i) => (
                      <div key={i} className="flex items-start">
                        {step.event_type.includes("FAILED") ? (
                           <XCircle className="w-4 h-4 mr-2 text-destructive shrink-0 mt-0.5" />
                        ) : step.event_type.includes("COMPLETED") || step.event_type.includes("RETRIEVED") || step.event_type === "COPILOT_REQUEST_STARTED" ? (
                           <CheckCircle2 className="w-4 h-4 mr-2 text-green-500 shrink-0 mt-0.5" />
                        ) : (
                           <Loader2 className="w-4 h-4 mr-2 text-primary animate-spin shrink-0 mt-0.5" />
                        )}
                        <div className="flex flex-col">
                          <span className={cn(
                             "font-semibold",
                             step.event_type.includes("FAILED") ? "text-destructive" : "text-foreground"
                          )}>
                             {step.payload.status || step.payload.message || 
                              (step.event_type.includes("TOOL") ? `Tool: ${step.payload.tool_name}` : step.event_type)}
                          </span>
                          {step.payload.latency_ms && (
                            <span className="text-muted-foreground text-[10px]">
                              Latency: {step.payload.latency_ms}ms
                            </span>
                          )}
                          {step.payload.error && (
                            <span className="text-destructive text-[10px]">
                              {step.payload.error}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex items-center">
                    <Loader2 className="w-5 h-5 mr-3 animate-spin text-primary" />
                    <div className="flex flex-col">
                      <span className="text-sm font-semibold text-foreground">Agent Orchestrator Active</span>
                      <span className="text-xs text-muted-foreground">Initializing investigation and awaiting real-time stream...</span>
                    </div>
                  </div>
                )}

              </div>
            </motion.div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-white/10 glass-panel">
          <form 
            onSubmit={(e) => { e.preventDefault(); handleSend(); }}
            className="flex items-center gap-2 max-w-4xl mx-auto relative"
          >
            <input 
              type="text" 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask Copilot about risk, anomalies, or simulate scenarios..."
              className="flex-1 rounded-full border border-white/10 bg-white/10 px-6 py-4 pr-16 text-sm focus:outline-none focus:ring-2 focus:ring-primary shadow-inner"
              disabled={loading}
            />
            <motion.button 
              whileTap={{ scale: 0.9 }}
              type="submit"
              disabled={!input.trim() || loading}
              className="absolute right-2 top-2 bottom-2 rounded-full p-2 bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors shadow-sm"
            >
              <Send className="w-5 h-5" />
            </motion.button>
          </form>
          <div className="mt-2 text-center text-[10px] text-muted-foreground font-mono">
            Orchestrator v2.0 | ReAct Protocol | Max Iterations: 5
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
}
