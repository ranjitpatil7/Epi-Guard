from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from typing import Dict, Any, List
from app.db.session import get_db
from app.models.domain import Region, RiskSnapshot, Alert
from app.services.risk_lineage_service import RiskLineageService
from app.services.risk_fusion_service import RiskFusionService
from app.services.cache_service import CacheService

router = APIRouter()

@router.get("/current", response_model=Dict[str, Any])
async def get_current_risk(db: AsyncSession = Depends(get_db)):
    """
    Returns the composite risk score and explanations for all regions.
    Cached for 5 minutes.
    """
    cache_key = "api:risk:current_all_v2"
    cached = await CacheService.get_cached(cache_key)
    if cached:
        return cached

    stmt = select(Region.id, Region.name)
    result = await db.execute(stmt)
    regions = result.all()
    
    target_date = datetime.now(timezone.utc)
    
    risk_data = []
    for r in regions:
        # Phase 4 ML Engine
        risk = await RiskFusionService.get_fused_risk(db, r.id, target_date)
        
        # Serialize datetime for JSON
        risk["calculation_timestamp"] = risk["calculation_timestamp"]
        risk["region_name"] = r.name
        
        risk_data.append(risk)
        
    response = {"data": risk_data}
    await CacheService.set_cached(cache_key, response, expire_seconds=300)
    return response

@router.post('/what-if', response_model=Dict[str, Any])
async def what_if_simulation(region_id: int, overrides: Dict[str, float], db: AsyncSession = Depends(get_db)):
    """Run a What-If scenario with overridden feature values through the ML pipeline."""
    target_date = datetime.now(timezone.utc)
    
    # Map frontend simple override keys to internal feature names
    feature_overrides = {}
    if 'rainfall' in overrides: feature_overrides['rainfall_7d'] = overrides['rainfall']
    if 'temperature' in overrides: feature_overrides['avg_temperature'] = overrides['temperature']
    if 'humidity' in overrides: feature_overrides['avg_humidity'] = overrides['humidity']
    if 'turbidity' in overrides: feature_overrides['avg_turbidity'] = overrides['turbidity']
    if 'ph' in overrides: feature_overrides['avg_ph'] = overrides['ph']
    if 'disease_cases' in overrides: feature_overrides['cases_14d'] = overrides['disease_cases']
    # Note: data quality and community severity might need custom handling,
    # but we can pass them in if supported.

    from app.services.risk_fusion_service import RiskFusionService
    risk_package = await RiskFusionService.get_fused_risk(db, region_id, target_date, feature_overrides)
    
    return {
        'region_id': region_id,
        'what_if_risk_score': risk_package["estimated_risk_score"],
        'what_if_risk_level': risk_package["risk_level"],
        'what_if_factors': risk_package["contributing_factors"],
        'full_risk_package': risk_package
    }

@router.get("/{region_id}/history", response_model=List[Dict[str, Any]])
async def get_risk_history(
    region_id: int, 
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(RiskSnapshot).where(RiskSnapshot.region_id == region_id).order_by(RiskSnapshot.timestamp.desc()).limit(limit)
    result = await db.execute(stmt)
    snapshots = result.scalars().all()
    
    return [
        {
            "snapshot_id": snap.snapshot_id,
            "timestamp": snap.timestamp,
            "current_risk": snap.current_risk,
            "previous_risk": snap.previous_risk,
            "risk_delta": snap.risk_delta,
            "confidence": snap.confidence
        }
        for snap in snapshots
    ]

@router.get("/{region_id}/snapshots/latest")
async def get_latest_risk_snapshot(region_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(RiskSnapshot).where(RiskSnapshot.region_id == region_id).order_by(RiskSnapshot.timestamp.desc()).limit(1)
    result = await db.execute(stmt)
    snapshot = result.scalar_one_or_none()
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="No risk snapshot found for region")
        
    return snapshot

@router.get("/snapshots/{snapshot_id}")
async def get_risk_snapshot(snapshot_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(RiskSnapshot).where(RiskSnapshot.snapshot_id == snapshot_id)
    result = await db.execute(stmt)
    snapshot = result.scalar_one_or_none()
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
        
    return snapshot

@router.get("/snapshots/{snapshot_id}/lineage")
async def get_risk_snapshot_lineage(snapshot_id: str, db: AsyncSession = Depends(get_db)):
    lineage = await RiskLineageService.get_snapshot_lineage(db, snapshot_id)
    if not lineage:
        raise HTTPException(status_code=404, detail="Lineage not found")
    return lineage

@router.get("/alerts/active")
async def get_active_alerts(
    region_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Alert).where(Alert.is_active == True)
    if region_id:
        stmt = stmt.where(Alert.region_id == region_id)
        
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/alerts/{alert_id}")
async def get_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.get("/alerts/{alert_id}/lineage")
async def get_alert_lineage(alert_id: int, db: AsyncSession = Depends(get_db)):
    lineage = await RiskLineageService.get_alert_lineage(db, alert_id)
    if not lineage:
        raise HTTPException(status_code=404, detail="Lineage not found")
    return lineage
