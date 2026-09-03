from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
from app.db.session import get_db
from app.models.domain import Anomaly

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
async def get_anomalies(
    db: AsyncSession = Depends(get_db),
    region_id: int = Query(None),
    limit: int = Query(50)
):
    """
    Fetch detected anomalies.
    """
    stmt = select(Anomaly).order_by(Anomaly.timestamp.desc())
    if region_id:
        stmt = stmt.where(Anomaly.region_id == region_id)
        
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    anomalies = result.scalars().all()
    
    return {
        "data": [
            {
                "id": a.id,
                "region_id": a.region_id,
                "feature": a.feature,
                "observed_value": a.observed_value,
                "expected_mean": a.expected_mean,
                "z_score": a.z_score,
                "severity": a.severity,
                "explanation": a.explanation,
                "timestamp": a.timestamp,
                "status": a.status
            } for a in anomalies
        ]
    }
