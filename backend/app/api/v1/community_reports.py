from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any
from app.db.session import get_db
from app.models.domain import CommunityReport, Region
from app.models.users import User
from app.core.auth_deps import get_current_user

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
async def get_reports(
    db: AsyncSession = Depends(get_db),
    region_id: int = Query(None),
    limit: int = Query(50),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch community reports with NLP severity and signals.
    """
    stmt = select(CommunityReport).order_by(CommunityReport.created_at.desc())
    
    effective_region_id = None
    
    if current_user.region_id is not None:
        if region_id is not None and region_id != current_user.region_id:
            raise HTTPException(status_code=403, detail="Not authorized to access reports for this region.")
        effective_region_id = current_user.region_id
    else:
        effective_region_id = region_id
        
    if effective_region_id is not None:
        # Check if region exists
        region_res = await db.execute(select(Region.id).where(Region.id == effective_region_id))
        if region_res.scalars().first() is None:
            raise HTTPException(status_code=404, detail="Region not found")
            
        stmt = stmt.join(
            Region, 
            func.ST_Contains(Region.geometry, CommunityReport.location)
        ).where(
            Region.id == effective_region_id,
            CommunityReport.location.is_not(None)
        )
    
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    reports = result.scalars().all()
    
    return {
        "data": [
            {
                "id": r.id,
                "text": r.text_content,
                "nlp_severity": r.nlp_severity,
                "status": r.status,
                "created_at": r.created_at
            } for r in reports
        ]
    }
