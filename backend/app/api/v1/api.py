from fastapi import APIRouter, Depends
from app.api.v1 import regions, risk, ml, alerts, anomalies, community_reports, data_quality, incidents, audit, forecasting, logistics, inventory, auth, users
from app.copilot import router as copilot_router
from app.core.auth_deps import require_permission
from app.core.permissions import Permission
from app.realtime.router import router as realtime_router

api_router = APIRouter()

# Auth router has its own specific endpoints (some public, some protected)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])

api_router.include_router(audit.router, prefix="/audit", tags=["audit"], dependencies=[Depends(require_permission(Permission.VIEW_AUDIT))])
api_router.include_router(regions.router, prefix="/regions", tags=["regions"], dependencies=[Depends(require_permission(Permission.VIEW_DASHBOARD))])
api_router.include_router(risk.router, prefix="/risk", tags=["risk"], dependencies=[Depends(require_permission(Permission.VIEW_RISK))])
api_router.include_router(ml.router, prefix="/ml", tags=["ml"], dependencies=[Depends(require_permission(Permission.VIEW_MODEL_INTELLIGENCE))])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"], dependencies=[Depends(require_permission(Permission.VIEW_ALERTS))])
api_router.include_router(anomalies.router, prefix="/anomalies", tags=["anomalies"], dependencies=[Depends(require_permission(Permission.VIEW_ANOMALIES))])
api_router.include_router(community_reports.router, prefix="/community-reports", tags=["community-reports"], dependencies=[Depends(require_permission(Permission.VIEW_COMMUNITY_REPORTS))])
api_router.include_router(data_quality.router, prefix="/data-quality", tags=["data-quality"], dependencies=[Depends(require_permission(Permission.VIEW_DATA_QUALITY))])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"], dependencies=[Depends(require_permission(Permission.VIEW_ALERTS))])
api_router.include_router(forecasting.router, prefix="/forecasting", tags=["forecasting"], dependencies=[Depends(require_permission(Permission.VIEW_SIR))])
api_router.include_router(logistics.router, prefix="/logistics", tags=["logistics"], dependencies=[Depends(require_permission(Permission.VIEW_ROUTES))])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"], dependencies=[Depends(require_permission(Permission.VIEW_SUPPLY_CHAIN))])
api_router.include_router(copilot_router, prefix="/copilot", tags=["copilot"], dependencies=[Depends(require_permission(Permission.USE_COPILOT))])

api_router.include_router(realtime_router, prefix="/realtime", tags=["realtime"])
