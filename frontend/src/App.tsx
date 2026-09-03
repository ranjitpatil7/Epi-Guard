import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Shell } from '@/components/layout/Shell'
import { ErrorBoundary } from '@/components/ui/error-boundary'
import { AuthProvider } from '@/lib/auth/AuthContext'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { PermissionGate } from '@/components/auth/PermissionGate'
import { Permission } from '@/lib/auth/permissions'
import { LoginPage } from '@/pages/auth/LoginPage'
import { UnauthorizedPage } from '@/pages/auth/UnauthorizedPage'

import Dashboard from '@/pages/dashboard/Dashboard'
import MapView from '@/pages/map/MapView'
import RegionalIntelligence from '@/pages/regional-intelligence/RegionalIntelligence'
import RegionalDetail from '@/pages/regional-intelligence/RegionalDetail'
import RiskAnalytics from '@/pages/risk/RiskAnalytics'
import AnomaliesCenter from '@/pages/anomalies/AnomaliesCenter'
import CommunityReports from '@/pages/community-reports/CommunityReports'
import AlertsCenter from '@/pages/alerts/AlertsCenter'
import DataQuality from '@/pages/data-quality/DataQuality'
import SimulationWorkspace from '@/pages/simulation/SimulationWorkspace'
import Copilot from '@/pages/copilot/Copilot'
import ModelIntelligence from '@/pages/model-intelligence/ModelIntelligence'
import AuditLog from '@/pages/audit/AuditLog'
import Settings from '@/pages/settings/Settings'
import SIRForecast from '@/pages/forecasting/SIRForecast'
import FleetRouting from '@/pages/logistics/FleetRouting'
import InventoryDashboard from '@/pages/inventory/InventoryDashboard'

import UserManagement from '@/pages/admin/UserManagement'

function App() {
  return (
    <BrowserRouter>
      <ErrorBoundary>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/unauthorized" element={<UnauthorizedPage />} />
            
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            
            <Route element={<ProtectedRoute />}>
              <Route element={<Shell />}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/map" element={<MapView />} />
                <Route path="/regional-intelligence" element={<RegionalIntelligence />} />
                <Route path="/regional-intelligence/:regionId" element={<RegionalDetail />} />
                <Route path="/risk" element={<RiskAnalytics />} />
                <Route path="/anomalies" element={<AnomaliesCenter />} />
                <Route path="/forecasting" element={<SIRForecast />} />
                <Route path="/logistics" element={<FleetRouting />} />
                <Route path="/inventory" element={<InventoryDashboard />} />
                <Route path="/community-reports" element={<CommunityReports />} />
                <Route path="/alerts" element={<AlertsCenter />} />
                <Route path="/data-quality" element={<DataQuality />} />
                <Route path="/simulation" element={<SimulationWorkspace />} />
                <Route path="/copilot" element={<Copilot />} />
                <Route path="/model-intelligence" element={<ModelIntelligence />} />
                <Route path="/audit" element={<AuditLog />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/admin/users" element={<PermissionGate permission={Permission.MANAGE_USERS} fallback={<Navigate to="/unauthorized" />}><UserManagement /></PermissionGate>} />
              </Route>
            </Route>
          </Routes>
        </AuthProvider>
      </ErrorBoundary>
    </BrowserRouter>
  )
}

export default App
