import { Outlet, useLocation } from "react-router-dom"
import { Sidebar } from "./Sidebar"
import { TopNav } from "./TopNav"
import { AlertCircle } from "lucide-react"
import { AnimatePresence } from "framer-motion"
import { PageWrapper } from "./PageWrapper"

export function Shell() {
  const location = useLocation()

  return (
    <div className="flex h-screen overflow-hidden bg-background p-2 sm:p-4 gap-4 relative z-0">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden rounded-[24px] border border-white/10 bg-black/40 backdrop-blur-3xl shadow-2xl relative z-10">
        <TopNav />
        
        {/* Public Health Disclaimer */}
        <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-2 flex items-center justify-center text-amber-500 text-xs font-medium shrink-0 shadow-inner">
          <AlertCircle className="w-4 h-4 mr-2 shrink-0" />
          <span className="truncate">JalRakshak AI is a public-health decision-support platform. Risk scores are estimates and should not be interpreted as medical diagnoses or definitive outbreak predictions.</span>
        </div>

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 custom-scrollbar">
          <AnimatePresence mode="wait">
            <PageWrapper key={location.pathname}>
              <Outlet />
            </PageWrapper>
          </AnimatePresence>
        </main>
      </div>
    </div>
  )
}
