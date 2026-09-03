import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.domain import Alert, RiskSnapshot, IntelligenceEvent

logger = logging.getLogger(__name__)

class RiskLineageService:
    """
    Traces the lineage of risk calculations from Alerts down to the source events.
    """
    
    @classmethod
    async def get_alert_lineage(cls, db: AsyncSession, alert_id: int) -> Optional[Dict[str, Any]]:
        stmt = select(Alert).where(Alert.id == alert_id)
        result = await db.execute(stmt)
        alert = result.scalar_one_or_none()
        
        if not alert:
            return None
            
        lineage = {
            "alert": {
                "id": alert.id,
                "severity": alert.severity,
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
                "updated_at": alert.updated_at.isoformat() if alert.updated_at else None,
            }
        }
        
        if alert.risk_snapshot_id:
            snapshot_lineage = await cls.get_snapshot_lineage(db, alert.risk_snapshot_id)
            if snapshot_lineage:
                lineage["risk_snapshot"] = snapshot_lineage
                
        return lineage
        
    @classmethod
    async def get_snapshot_lineage(cls, db: AsyncSession, snapshot_id: str) -> Optional[Dict[str, Any]]:
        stmt = select(RiskSnapshot).where(RiskSnapshot.snapshot_id == snapshot_id)
        result = await db.execute(stmt)
        snapshot = result.scalar_one_or_none()
        
        if not snapshot:
            return None
            
        lineage = {
            "snapshot_id": snapshot.snapshot_id,
            "region_id": snapshot.region_id,
            "timestamp": snapshot.timestamp.isoformat() if snapshot.timestamp else None,
            "current_risk": snapshot.current_risk,
            "previous_risk": snapshot.previous_risk,
            "risk_delta": snapshot.risk_delta,
            "model_version": snapshot.model_version,
            "feature_snapshot": snapshot.feature_snapshot,
            "explanation": snapshot.explanation_metadata
        }
        
        if snapshot.triggering_event_id:
            stmt_event = select(IntelligenceEvent).where(IntelligenceEvent.event_id == snapshot.triggering_event_id)
            res_event = await db.execute(stmt_event)
            event = res_event.scalar_one_or_none()
            
            if event:
                lineage["triggering_event"] = {
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "source": event.source,
                    "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                    "payload": event.payload
                }
                
        return lineage
