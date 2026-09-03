from enum import Enum
from typing import Set, Dict
from app.models.users import UserRole

class PermissionCategory(str, Enum):
    DASHBOARD = "Dashboard"
    MAP = "Map"
    ANALYTICS = "Analytics"
    FORECASTING = "Forecasting"
    LOGISTICS = "Logistics"
    REPORTS = "Reports"
    COPILOT = "AI Copilot"
    ADMINISTRATION = "Administration"

class Permission(str, Enum):
    # Dashboard
    VIEW_DASHBOARD = "VIEW_DASHBOARD"
    
    # Map
    VIEW_MAP = "VIEW_MAP"
    
    # Analytics
    VIEW_RISK = "VIEW_RISK"
    VIEW_ANOMALIES = "VIEW_ANOMALIES"
    VIEW_ALERTS = "VIEW_ALERTS"
    VIEW_MODEL_INTELLIGENCE = "VIEW_MODEL_INTELLIGENCE"
    
    # Forecasting
    VIEW_SIR = "VIEW_SIR"
    RUN_SIMULATION = "RUN_SIMULATION"
    
    # Logistics
    VIEW_ROUTES = "VIEW_ROUTES"
    VIEW_SUPPLY_CHAIN = "VIEW_SUPPLY_CHAIN"
    UPDATE_INCIDENT = "UPDATE_INCIDENT"
    
    # Reports
    VIEW_COMMUNITY_REPORTS = "VIEW_COMMUNITY_REPORTS"
    SUBMIT_REPORT = "SUBMIT_REPORT"
    VIEW_DATA_QUALITY = "VIEW_DATA_QUALITY"
    
    # Copilot
    USE_COPILOT = "USE_COPILOT"
    
    # Administration
    VIEW_AUDIT = "VIEW_AUDIT"
    MANAGE_USERS = "MANAGE_USERS"
    MANAGE_SETTINGS = "MANAGE_SETTINGS"

# Mapping permissions to categories for UI grouping (e.g. Admin panel checkboxes)
PERMISSION_METADATA: Dict[Permission, PermissionCategory] = {
    Permission.VIEW_DASHBOARD: PermissionCategory.DASHBOARD,
    
    Permission.VIEW_MAP: PermissionCategory.MAP,
    
    Permission.VIEW_RISK: PermissionCategory.ANALYTICS,
    Permission.VIEW_ANOMALIES: PermissionCategory.ANALYTICS,
    Permission.VIEW_ALERTS: PermissionCategory.ANALYTICS,
    Permission.VIEW_MODEL_INTELLIGENCE: PermissionCategory.ANALYTICS,
    
    Permission.VIEW_SIR: PermissionCategory.FORECASTING,
    Permission.RUN_SIMULATION: PermissionCategory.FORECASTING,
    
    Permission.VIEW_ROUTES: PermissionCategory.LOGISTICS,
    Permission.VIEW_SUPPLY_CHAIN: PermissionCategory.LOGISTICS,
    Permission.UPDATE_INCIDENT: PermissionCategory.LOGISTICS,
    
    Permission.VIEW_COMMUNITY_REPORTS: PermissionCategory.REPORTS,
    Permission.SUBMIT_REPORT: PermissionCategory.REPORTS,
    Permission.VIEW_DATA_QUALITY: PermissionCategory.REPORTS,
    
    Permission.USE_COPILOT: PermissionCategory.COPILOT,
    
    Permission.VIEW_AUDIT: PermissionCategory.ADMINISTRATION,
    Permission.MANAGE_USERS: PermissionCategory.ADMINISTRATION,
    Permission.MANAGE_SETTINGS: PermissionCategory.ADMINISTRATION,
}

# The core Role-Based Access Control matrix
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.GOVERNMENT_OFFICIAL: {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_MAP,
        Permission.VIEW_RISK,
        Permission.VIEW_ANOMALIES,
        Permission.VIEW_ALERTS,
        Permission.VIEW_ROUTES,
        Permission.VIEW_SUPPLY_CHAIN,
        Permission.VIEW_COMMUNITY_REPORTS,
        Permission.USE_COPILOT,
        Permission.MANAGE_SETTINGS,
    },
    UserRole.EPIDEMIOLOGIST: {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_MAP,         # Read-only visually, but needs endpoint access
        Permission.VIEW_RISK,
        Permission.VIEW_ANOMALIES,
        Permission.VIEW_ALERTS,
        Permission.VIEW_MODEL_INTELLIGENCE,
        Permission.VIEW_SIR,
        Permission.RUN_SIMULATION,
        Permission.VIEW_COMMUNITY_REPORTS,
        Permission.VIEW_DATA_QUALITY,
        Permission.USE_COPILOT,
        Permission.MANAGE_SETTINGS,
    },
    UserRole.FIELD_OFFICER: {
        Permission.VIEW_MAP,
        Permission.VIEW_ALERTS,
        Permission.VIEW_ROUTES,
        Permission.VIEW_SUPPLY_CHAIN,
        Permission.UPDATE_INCIDENT,
        Permission.VIEW_COMMUNITY_REPORTS,
        Permission.SUBMIT_REPORT,
        Permission.USE_COPILOT,
        Permission.MANAGE_SETTINGS,
    },
    UserRole.ADMINISTRATOR: set(Permission) # Administrators have all permissions
}

def get_permissions_for_role(role: UserRole) -> Set[Permission]:
    return ROLE_PERMISSIONS.get(role, set())
