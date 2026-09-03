import { Link, useLocation } from "react-router-dom"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"
import { 
  LayoutDashboard, 
  Map, 
  MapPin, 
  Activity,
  AlertTriangle,
  FileText,
  ShieldCheck,
  BrainCircuit,
  Bot,
  Settings,
  History,
  LineChart,
  Truck,
  Package,
  LogOut
} from "lucide-react"
import { useAuth } from "@/lib/auth/AuthContext"
import { Permission } from "@/lib/auth/permissions"

const navigation = [
  { name: 'Command Center', href: '/dashboard', icon: LayoutDashboard, permission: Permission.VIEW_DASHBOARD },
  { name: 'Intelligence Map', href: '/map', icon: Map, permission: Permission.VIEW_MAP },
  { name: 'Regional Intelligence', href: '/regional-intelligence', icon: MapPin, permission: Permission.VIEW_DASHBOARD },
  { name: 'Risk Analytics', href: '/risk', icon: Activity, permission: Permission.VIEW_RISK },
  { name: 'Anomalies', href: '/anomalies', icon: Activity, permission: Permission.VIEW_ANOMALIES },
  { name: 'Alerts', href: '/alerts', icon: AlertTriangle, permission: Permission.VIEW_ALERTS },
  { name: 'SIR Forecasting', href: '/forecasting', icon: LineChart, permission: Permission.VIEW_SIR },
  { name: 'Fleet Routing', href: '/logistics', icon: Truck, permission: Permission.VIEW_ROUTES },
  { name: 'Supply Chain', href: '/inventory', icon: Package, permission: Permission.VIEW_SUPPLY_CHAIN },
  { name: 'Community Reports', href: '/community-reports', icon: FileText, permission: Permission.VIEW_COMMUNITY_REPORTS },
  { name: 'Data Quality', href: '/data-quality', icon: ShieldCheck, permission: Permission.VIEW_DATA_QUALITY },
  { name: 'What-If Simulator', href: '/simulation', icon: BrainCircuit, permission: Permission.RUN_SIMULATION },
  { name: 'AI Copilot', href: '/copilot', icon: Bot, permission: Permission.USE_COPILOT },
  { name: 'Model Intelligence', href: '/model-intelligence', icon: BrainCircuit, permission: Permission.VIEW_MODEL_INTELLIGENCE },
  { name: 'Audit Log', href: '/audit', icon: History, permission: Permission.VIEW_AUDIT },
  { name: 'User Management', href: '/admin/users', icon: ShieldCheck, permission: Permission.MANAGE_USERS },
  { name: 'Settings', href: '/settings', icon: Settings, permission: Permission.MANAGE_SETTINGS },
]

export function Sidebar() {
  const location = useLocation()
  const { user, hasPermission, logout } = useAuth()

  return (
    <div className="flex h-full w-64 flex-col rounded-[24px] bg-white/5 backdrop-blur-3xl shadow-[0_8px_32px_rgba(0,0,0,0.4)] border border-white/10 z-20 overflow-hidden relative">
      <div className="flex h-20 items-center px-6 border-b border-white/10 relative z-10">
        <div className="h-10 w-10 rounded-[14px] bg-gradient-to-br from-primary/80 to-purple-600/80 border border-white/20 p-2 mr-3 shadow-[0_0_15px_rgba(59,130,246,0.5)] flex items-center justify-center">
          <ShieldCheck className="h-6 w-6 text-white drop-shadow-md" />
        </div>
        <span className="text-xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white to-white/60">JalRakshak</span>
      </div>
      <div className="flex-1 overflow-y-auto py-6 relative z-10 custom-scrollbar">
        <nav className="space-y-1.5 px-4 relative">
          {navigation.filter(item => hasPermission(item.permission)).map((item) => {
            const isActive = location.pathname.startsWith(item.href)
            return (
              <div key={item.name} className="relative">
                {isActive && (
                  <motion.div
                    layoutId="sidebar-active-indicator"
                    className="absolute inset-0 rounded-xl bg-white/10 border border-white/10 shadow-[inset_0_1px_0_rgba(255,255,255,0.2)] z-0"
                    initial={false}
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                  />
                )}
                <Link
                  to={item.href}
                  className={cn(
                    "relative z-10 group flex items-center px-3 py-2.5 text-[15px] rounded-xl transition-all duration-300",
                    isActive ? "text-primary-foreground font-semibold" : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  <item.icon
                    className={cn(
                      "mr-3 flex-shrink-0 h-5 w-5 transition-colors duration-300",
                      isActive ? "text-primary-foreground drop-shadow-[0_0_8px_rgba(255,255,255,0.5)]" : "text-muted-foreground group-hover:text-foreground/80"
                    )}
                    aria-hidden="true"
                  />
                  <span className="truncate">{item.name}</span>
                </Link>
              </div>
            )
          })}
        </nav>
      </div>
      
      {/* User Card */}
      <div className="p-4 border-t border-white/10 bg-black/40 backdrop-blur-md relative z-10">
        {user ? (
          <div className="flex flex-col">
            <div className="flex items-center justify-between mb-2">
              <span className="font-semibold text-sm text-foreground/90 truncate">{user.full_name}</span>
              <button onClick={logout} className="text-muted-foreground hover:text-red-400 transition-colors" title="Logout">
                <LogOut className="h-4 w-4" />
              </button>
            </div>
            <span className="text-[10px] text-primary-foreground/70 tracking-wider font-mono bg-primary/20 px-2 py-0.5 rounded-sm inline-block w-max mb-2">
              {user.role.replace('_', ' ')}
            </span>
            <div className="text-xs text-muted-foreground truncate mb-2">
              {user.region_id ? `Region ID: ${user.region_id}` : 'National Scope'}
            </div>
            <div className="font-medium text-xs text-green-400 flex items-center mt-1">
              <span className="relative flex h-2 w-2 mr-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500 shadow-[0_0_8px_rgba(74,222,128,0.8)]"></span>
              </span>
              System Operational
            </div>
          </div>
        ) : (
          <div className="animate-pulse flex space-x-4">
            <div className="flex-1 space-y-3 py-1">
              <div className="h-2 bg-slate-700 rounded w-3/4"></div>
              <div className="space-y-2">
                <div className="h-2 bg-slate-700 rounded"></div>
                <div className="h-2 bg-slate-700 rounded w-5/6"></div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
