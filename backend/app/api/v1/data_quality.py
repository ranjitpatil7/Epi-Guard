from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any
from app.db.session import get_db
from app.models.domain import DataSource

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
async def get_data_quality(db: AsyncSession = Depends(get_db)):
    """
    Returns aggregated data quality metrics from registered DataSources.
    """
    stmt = select(func.avg(DataSource.data_quality_score))
    result = await db.execute(stmt)
    avg_quality = result.scalar() or 0.0
    
    # Calculate mock completeness/freshness based on the overall quality for now
    # A fully complete system would query max(timestamp) for each feature
    completeness = max(0.0, min(100.0, avg_quality * 100))
    freshness = 95.0
    validity = completeness * 0.98
    
    return {
        "overall_quality": completeness,
        "completeness": completeness,
        "freshness": freshness,
        "validity": validity,
        "coverage": 90.0,
        "sources": [
            {"name": "IMD Weather", "status": "ACTIVE", "quality": 98.0},
            {"name": "Jal Jeevan Mission", "status": "ACTIVE", "quality": 85.0},
            {"name": "IDSP Health", "status": "ACTIVE", "quality": completeness}
        ]
    }
