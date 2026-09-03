import os
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.domain import IntelligenceEvent, RiskSnapshot
from app.services.risk_fusion_service import RiskFusionService
from app.services.risk_recalculation_coordinator import RiskRecalculationCoordinator
from app.db.session import AsyncSessionLocal
from app.realtime.publisher import EventPublisher
from app.realtime.ws_broadcaster import broadcast_ws_event
from app.realtime.ws_events import WSEventType

logger = logging.getLogger(__name__)

MAX_PROCESSING_DEPTH = int(os.getenv("MAX_EVENT_PROCESSING_DEPTH", "3"))

class EventDrivenRiskService:
    
    RELEVANT_EVENT_TYPES = {
        "RAINFALL_UPDATE",
        "WATER_QUALITY_UPDATE",
        "DISEASE_CASE_UPDATE",
        "COMMUNITY_REPORT",
        "ANOMALY_DETECTED",
        "MODEL_DRIFT_DETECTED"
    }

    @classmethod
    def should_recalculate(cls, event: IntelligenceEvent) -> bool:
        if event.event_type not in cls.RELEVANT_EVENT_TYPES:
            return False
            
        # Check processing depth to prevent recursive loops
        depth = 0
        if isinstance(event.payload, dict) and "lineage" in event.payload:
            depth = event.payload.get("lineage", {}).get("processing_depth", 0)
            
        if depth >= MAX_PROCESSING_DEPTH:
            logger.warning(f"Event {event.event_id} reached MAX_PROCESSING_DEPTH ({depth}). Dropping recalculation.")
            return False
            
        return True
        
    @classmethod
    async def trigger_recalculation(cls, event: IntelligenceEvent):
        if not cls.should_recalculate(event):
            return
            
        # Determine if it's high priority (bypass debounce)
        is_critical = False
        if event.event_type in ["ANOMALY_DETECTED", "MODEL_DRIFT_DETECTED"]:
            if isinstance(event.payload, dict):
                sev = event.payload.get("severity", "")
                if sev in ["CRITICAL", "HIGH"]:
                    is_critical = True

        await RiskRecalculationCoordinator.schedule_recalculation(
            region_id=event.region_id,
            event=event,
            callback=cls._async_recalculate_callback,
            bypass_debounce=is_critical
        )
        
    @classmethod
    async def _async_recalculate_callback(cls, region_id: int, event: IntelligenceEvent):
        async with AsyncSessionLocal() as db:
            await cls.recalculate_region_risk(db, region_id, event)
            
    @classmethod
    async def recalculate_region_risk(cls, db: AsyncSession, region_id: int, triggering_event: IntelligenceEvent):
        now = datetime.now(timezone.utc)
        
        # Get previous risk to calculate delta
        stmt = select(RiskSnapshot).where(RiskSnapshot.region_id == region_id).order_by(RiskSnapshot.timestamp.desc()).limit(1)
        result = await db.execute(stmt)
        previous_snapshot = result.scalar_one_or_none()
        previous_risk = previous_snapshot.current_risk if previous_snapshot else 0.0
        
        # Execute risk fusion pipeline
        risk_result = await RiskFusionService.get_fused_risk(db, region_id, now)
        
        current_risk = risk_result["estimated_risk_score"]
        risk_delta = current_risk - previous_risk
        
        # Save Snapshot
        snapshot_id = f"snap_{uuid.uuid4().hex[:16]}"
        
        snapshot = RiskSnapshot(
            snapshot_id=snapshot_id,
            region_id=region_id,
            timestamp=now,
            current_risk=current_risk,
            previous_risk=previous_risk,
            risk_delta=risk_delta,
            ensemble_prediction=risk_result.get("model_predictions", {}).get("Ensemble", current_risk),
            lower_bound=risk_result.get("uncertainty", {}).get("lower", current_risk),
            upper_bound=risk_result.get("uncertainty", {}).get("upper", current_risk),
            confidence=risk_result.get("confidence_score", 0.0) / 100.0,
            model_version=risk_result.get("model_version", "unknown"),
            triggering_event_id=triggering_event.event_id,
            triggering_event_type=triggering_event.event_type,
            feature_snapshot=risk_result.get("features_used", {}),
            explanation_metadata={
                "uncertainty_explanation": risk_result.get("uncertainty_explanation", ""),
                "contributing_factors": risk_result.get("contributing_factors", {})
            }
        )
        db.add(snapshot)
        await db.commit()
        await db.refresh(snapshot)
        
        # Categorize change
        change_type = "STABLE"
        if risk_delta > 15.0:
            change_type = "RAPID_ESCALATION"
        elif risk_delta > 5.0:
            change_type = "MODERATE_INCREASE"
        elif risk_delta > 1.0:
            change_type = "MINOR_INCREASE"
        elif risk_delta < -15.0:
            change_type = "SIGNIFICANT_DECREASE"
        elif risk_delta < -5.0:
            change_type = "MINOR_DECREASE"
            
        # Determine lineage
        depth = 0
        if isinstance(triggering_event.payload, dict) and "lineage" in triggering_event.payload:
            depth = triggering_event.payload.get("lineage", {}).get("processing_depth", 0)
            
        lineage = {
            "origin_event_id": triggering_event.event_id,
            "caused_by": "EventDrivenRiskService",
            "processing_depth": depth + 1
        }
        
        event_type = "RISK_RECALCULATED"
        if change_type in ["RAPID_ESCALATION", "MODERATE_INCREASE"]:
            event_type = "RISK_ESCALATED"
        elif change_type in ["SIGNIFICANT_DECREASE", "MINOR_DECREASE"]:
            event_type = "RISK_DEESCALATED"
            
        # Publish Risk Event
        payload = {
            "region_id": region_id,
            "snapshot_id": snapshot_id,
            "current_risk": current_risk,
            "previous_risk": previous_risk,
            "risk_delta": risk_delta,
            "change_type": change_type,
            "confidence": snapshot.confidence,
            "prediction_interval": {
                "lower": snapshot.lower_bound,
                "upper": snapshot.upper_bound
            },
            "lineage": lineage
        }
        
        await EventPublisher.publish_event(
            event_type=event_type,
            region_id=region_id,
            source="EventDrivenRiskService",
            payload=payload
        )
        # WS broadcast (transient delivery, AFTER commit)
        await broadcast_ws_event(
            event_type=WSEventType.RISK_RECALCULATED,
            region_id=region_id,
            severity="HIGH" if current_risk >= 80 else "WARNING" if current_risk >= 60 else "INFO",
            payload={
                "snapshot_id": snapshot_id,
                "current_risk": current_risk,
                "previous_risk": previous_risk,
                "risk_delta": risk_delta,
                "change_type": change_type,
                "confidence": snapshot.confidence,
            },
        )
