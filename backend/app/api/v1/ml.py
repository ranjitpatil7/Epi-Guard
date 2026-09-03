from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from typing import Dict, Any, List
from app.db.session import get_db
from app.services.risk_fusion_service import RiskFusionService
from app.models.domain import ModelVersion, MLPredictionHistory, ModelDriftEvent

router = APIRouter()

@router.get("/risk/{region_id}", response_model=Dict[str, Any])
async def get_ml_risk(region_id: int, db: AsyncSession = Depends(get_db)):
    """
    Returns the fused ML risk prediction, explanations, and forecasts for a region.
    """
    target_date = datetime.now(timezone.utc)
    risk_package = await RiskFusionService.get_fused_risk(db, region_id, target_date)
    return risk_package

@router.get("/model/active", response_model=Dict[str, Any])
async def get_active_model(db: AsyncSession = Depends(get_db)):
    """
    Returns metadata for the currently active ML model version.
    """
    stmt = select(ModelVersion).order_by(ModelVersion.training_date.desc()).limit(1)
    result = await db.execute(stmt)
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(status_code=404, detail="No active model found")
        
    return {
        "version": model.version,
        "training_date": model.training_date,
        "metrics": {
            "r2_calibration": model.calibration
        },
        "dataset_version": model.dataset_version
    }

@router.get("/predictions/history", response_model=Dict[str, Any])
async def get_prediction_history(db: AsyncSession = Depends(get_db)):
    """
    Returns recent ML prediction history.
    """
    stmt = select(MLPredictionHistory).order_by(MLPredictionHistory.prediction_timestamp.desc()).limit(50)
    result = await db.execute(stmt)
    history = result.scalars().all()
    
    return {
        "data": [
            {
                "region_id": h.region_id,
                "timestamp": h.prediction_timestamp,
                "predicted_risk": h.predicted_risk,
                "model_version": h.model_version
            } for h in history
        ]
    }

@router.get("/model/drift", response_model=Dict[str, Any])
async def get_model_drift(db: AsyncSession = Depends(get_db)):
    """
    Returns recent model drift monitoring events.
    """
    stmt = select(ModelDriftEvent).order_by(ModelDriftEvent.timestamp.desc()).limit(20)
    result = await db.execute(stmt)
    events = result.scalars().all()
    
    return {
        "events": [
            {
                "feature": e.feature_name,
                "score": e.drift_score,
                "status": e.status,
                "timestamp": e.timestamp
            } for e in events
        ]
    }
