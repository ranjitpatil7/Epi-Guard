from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Dict, Any, List
from app.db.session import get_db
from app.models.domain import Alert, AuditLog
from datetime import datetime, timezone

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
async def get_alerts(
    db: AsyncSession = Depends(get_db),
    active_only: bool = Query(True),
    limit: int = Query(50)
):
    """
    Fetch system alerts (Early Warnings).
    """
    stmt = select(Alert).order_by(Alert.created_at.desc())
    if active_only:
        stmt = stmt.where(Alert.is_active == True)
        
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    alerts = result.scalars().all()
    
    return {
        "data": [
            {
                "id": a.id,
                "region_id": a.region_id,
                "severity": a.severity,
                "message": a.message,
                "is_active": a.is_active,
                "created_at": a.created_at,
                "updated_at": a.updated_at
            } for a in alerts
        ]
    }

@router.post("/{alert_id}/acknowledge", response_model=Dict[str, Any])
async def acknowledge_alert(
    alert_id: int, 
    db: AsyncSession = Depends(get_db),
    # In a real app we would depend on get_current_user to check RBAC.
    # user = Depends(get_current_user) 
):
    """
    Acknowledge/Resolve an alert. (RBAC protected in production)
    """
    # 1. Fetch Alert
    stmt = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    # 2. Update Status
    alert.is_active = False
    alert.updated_at = datetime.now(timezone.utc)
    
    # 3. Create Audit Log
    # audit = AuditLog(user_id=user.id, action=f"Acknowledged alert {alert_id}", ip_address="API")
    # db.add(audit)
    
    await db.commit()
    
    return {"status": "success", "message": f"Alert {alert_id} acknowledged"}
