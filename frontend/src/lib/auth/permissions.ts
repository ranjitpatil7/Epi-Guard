export enum Permission {
  // Dashboard
  VIEW_DASHBOARD = "VIEW_DASHBOARD",
  
  // Map
  VIEW_MAP = "VIEW_MAP",
  
  // Analytics
  VIEW_RISK = "VIEW_RISK",
  VIEW_ANOMALIES = "VIEW_ANOMALIES",
  VIEW_ALERTS = "VIEW_ALERTS",
  VIEW_MODEL_INTELLIGENCE = "VIEW_MODEL_INTELLIGENCE",
  
  // Forecasting
  VIEW_SIR = "VIEW_SIR",
  RUN_SIMULATION = "RUN_SIMULATION",
  
  // Logistics
  VIEW_ROUTES = "VIEW_ROUTES",
  VIEW_SUPPLY_CHAIN = "VIEW_SUPPLY_CHAIN",
  UPDATE_INCIDENT = "UPDATE_INCIDENT",
  
  // Reports
  VIEW_COMMUNITY_REPORTS = "VIEW_COMMUNITY_REPORTS",
  SUBMIT_REPORT = "SUBMIT_REPORT",
  VIEW_DATA_QUALITY = "VIEW_DATA_QUALITY",
  
  // Copilot
  USE_COPILOT = "USE_COPILOT",
  
  // Administration
  VIEW_AUDIT = "VIEW_AUDIT",
  MANAGE_USERS = "MANAGE_USERS",
  MANAGE_SETTINGS = "MANAGE_SETTINGS"
}

export interface User {
  id: number;
  username: string;
  email?: string;
  full_name: string;
  role: string;
  region_id: number | null;
  status: string;
  permissions: Permission[];
}
