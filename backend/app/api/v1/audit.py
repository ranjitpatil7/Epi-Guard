from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
from app.db.session import get_db
from app.models.domain import AuditLog

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
async def get_audit_logs(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50)
):
    """
    Fetch system audit logs.
    """
    stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    return {
        "data": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "ip_address": log.ip_address,
                "timestamp": log.timestamp
            } for log in logs
        ]
    }
