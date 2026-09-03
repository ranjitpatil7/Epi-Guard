import logging
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.domain import IntelligenceIncident, IncidentStatus
from app.cep.schemas import IntelligenceIncidentResponse
from app.cep.incident_service import IncidentService
from app.realtime.event_schema import IntelligenceEvent
from app.cep.engine import CEPEngine
from datetime import datetime, timezone
import uuid
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)

async def get_db():
    async with AsyncSessionLocal() as db:
        yield db

@router.get("/", response_model=List[IntelligenceIncidentResponse])
async def read_incidents(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve incidents.
    """
    stmt = select(IntelligenceIncident).order_by(IntelligenceIncident.first_detected_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    incidents = result.scalars().all()
    return incidents

@router.get("/{incident_id}", response_model=IntelligenceIncidentResponse)
async def read_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get incident by ID.
    """
    stmt = select(IntelligenceIncident).where(IntelligenceIncident.incident_id == incident_id)
    result = await db.execute(stmt)
    incident = result.scalar_one_or_none()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@router.post("/{incident_id}/acknowledge", response_model=IntelligenceIncidentResponse)
async def acknowledge_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Transition incident to INVESTIGATING.
    """
    try:
        incident = await IncidentService.transition_status(db, incident_id, IncidentStatus.INVESTIGATING)
        return incident
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{incident_id}/resolve", response_model=IntelligenceIncidentResponse)
async def resolve_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Transition incident to RESOLVED.
    """
    try:
        incident = await IncidentService.transition_status(db, incident_id, IncidentStatus.RESOLVED)
        return incident
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/demo")
async def trigger_demo(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Trigger deterministic demo scenario for COMPOUND_RISK_EVENT.
    """
    cep_engine = CEPEngine()
    base_time = datetime.now(timezone.utc)
    region_id = 1 # Assam
    
    events = [
        IntelligenceEvent(
            event_id=f"demo-env-{uuid.uuid4()}",
            event_type="RAINFALL_UPDATE",
            region_id=region_id,
            source="demo_system",
            timestamp=base_time,
            payload={"rainfall": 150.0},
            correlation_id="demo-correlation"
        ),
        IntelligenceEvent(
            event_id=f"demo-wq-{uuid.uuid4()}",
            event_type="WATER_QUALITY_UPDATE",
            region_id=region_id,
            source="demo_system",
            timestamp=base_time,
            payload={"wqi": 30.0},
            correlation_id="demo-correlation"
        ),
        IntelligenceEvent(
            event_id=f"demo-anom-{uuid.uuid4()}",
            event_type="ANOMALY_DETECTED",
            region_id=region_id,
            source="demo_system",
            timestamp=base_time,
            payload={"anomaly_score": 0.95},
            correlation_id="demo-correlation"
        ),
        IntelligenceEvent(
            event_id=f"demo-risk-{uuid.uuid4()}",
            event_type="RISK_CHANGED",
            region_id=region_id,
            source="demo_system",
            timestamp=base_time,
            payload={"risk_score": 0.85, "risk_delta": 0.3},
            correlation_id="demo-correlation"
        )
    ]
    
    from app.realtime.event_bus import EventBus
    
    for e in events:
        await EventBus.publish(e)
        
    return {"message": "Demo events processed successfully", "events_triggered": len(events), "warning": "SYNTHETIC VALIDATION DATA"}
