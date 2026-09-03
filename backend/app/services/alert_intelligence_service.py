import os
import hashlib
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from app.models.domain import Alert
from app.realtime.publisher import EventPublisher
from app.realtime.ws_broadcaster import broadcast_ws_event
from app.realtime.ws_events import WSEventType

logger = logging.getLogger(__name__)

class AlertIntelligenceService:
    
    COOLDOWN_MINUTES = {
        "INFO": int(os.getenv("ALERT_COOLDOWN_INFO", "60")),
        "WARNING": int(os.getenv("ALERT_COOLDOWN_WARNING", "30")),
        "HIGH": int(os.getenv("ALERT_COOLDOWN_HIGH", "15")),
        "CRITICAL": int(os.getenv("ALERT_COOLDOWN_CRITICAL", "5"))
    }
    
    SEVERITY_RANKS = {
        "INFO": 1,
        "WARNING": 2,
        "HIGH": 3,
        "CRITICAL": 4
    }
    
    @classmethod
    def generate_fingerprint(cls, region_id: int, alert_type: str, severity: str, trigger_class: str, time_bucket_hours: int = 1) -> str:
        """Generates a stable, deterministic hash for deduplicating identical alerts in a given time window."""
        now = datetime.now(timezone.utc)
        bucket = now.replace(minute=0, second=0, microsecond=0)
        # Group by hours if time_bucket_hours > 1
        bucket = bucket - timedelta(hours=bucket.hour % time_bucket_hours)
        
        fingerprint_data = f"{region_id}:{alert_type}:{severity}:{trigger_class}:{bucket.isoformat()}"
        return hashlib.md5(fingerprint_data.encode()).hexdigest()

    @classmethod
    async def evaluate_risk_event(cls, db: AsyncSession, risk_payload: Dict[str, Any]) -> Optional[Alert]:
        """Evaluates a RISK_RECALCULATED, RISK_ESCALATED, or RISK_DEESCALATED event to generate or update alerts."""
        region_id = risk_payload["region_id"]
        current_risk = risk_payload["current_risk"]
        change_type = risk_payload.get("change_type", "STABLE")
        snapshot_id = risk_payload.get("snapshot_id")
        
        # Determine target severity
        target_severity = cls._determine_severity(current_risk, change_type)
        
        if not target_severity:
            return await cls._attempt_resolution(db, region_id)
            
        # Get active alert for region
        stmt = select(Alert).where(Alert.region_id == region_id, Alert.is_active == True)
        result = await db.execute(stmt)
        active_alert = result.scalars().first()
        
        if active_alert:
            return await cls._handle_existing_alert(db, active_alert, target_severity, risk_payload)
        else:
            return await cls._create_new_alert(db, region_id, target_severity, risk_payload)
            
    @classmethod
    def _determine_severity(cls, current_risk: float, change_type: str) -> Optional[str]:
        if current_risk >= 80.0 or change_type == "RAPID_ESCALATION":
            return "CRITICAL"
        if current_risk >= 60.0 or change_type == "MODERATE_INCREASE":
            return "HIGH"
        if current_risk >= 40.0:
            return "WARNING"
        if current_risk >= 20.0:
            return "INFO"
        return None # Below 20.0, no active alert needed
        
    @classmethod
    async def _handle_existing_alert(cls, db: AsyncSession, alert: Alert, target_severity: str, payload: Dict[str, Any]) -> Optional[Alert]:
        current_rank = cls.SEVERITY_RANKS.get(alert.severity, 0)
        target_rank = cls.SEVERITY_RANKS.get(target_severity, 0)
        
        now = datetime.now(timezone.utc)
        
        # Check Cooldown
        cooldown_mins = cls.COOLDOWN_MINUTES.get(alert.severity, 60)
        if alert.updated_at and (now - alert.updated_at).total_seconds() < (cooldown_mins * 60):
            if target_rank <= current_rank:
                # Still cooling down, and not an escalation. Suppress.
                return None
        
        if target_rank > current_rank:
            # ESCALATION
            alert.severity = target_severity
            alert.message = f"Risk escalated to {target_severity} (Score: {payload['current_risk']:.1f})"
            event_type = "ALERT_ESCALATED"
        elif target_rank < current_rank:
            # DE-ESCALATION
            alert.severity = target_severity
            alert.message = f"Risk de-escalated to {target_severity} (Score: {payload['current_risk']:.1f})"
            event_type = "ALERT_DEESCALATED"
        else:
            # SAME SEVERITY (Refresh)
            # We already passed the cooldown check, so we can emit an update if we want, but usually we just update the DB
            alert.message = f"Risk remains {target_severity} (Score: {payload['current_risk']:.1f})"
            event_type = "ALERT_UPDATED"
            
        alert.updated_at = now
        alert.confidence = payload.get("confidence", alert.confidence)
        alert.prediction_interval = payload.get("prediction_interval", alert.prediction_interval)
        alert.risk_snapshot_id = payload.get("snapshot_id", alert.risk_snapshot_id)
        
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        
        await cls._publish_alert_event(event_type, alert)
        # WS broadcast after successful commit
        await broadcast_ws_event(
            event_type=event_type,
            region_id=alert.region_id,
            severity=alert.severity,
            payload={
                "alert_id": alert.id,
                "severity": alert.severity,
                "message": alert.message,
                "confidence": alert.confidence,
            },
        )
        return alert

    @classmethod
    async def _create_new_alert(cls, db: AsyncSession, region_id: int, severity: str, payload: Dict[str, Any]) -> Optional[Alert]:
        trigger_class = payload.get("change_type", "UNKNOWN")
        fingerprint = cls.generate_fingerprint(region_id, "RISK_ALERT", severity, trigger_class)
        
        new_alert = Alert(
            region_id=region_id,
            severity=severity,
            message=f"New {severity} risk alert (Score: {payload['current_risk']:.1f})",
            is_active=True,
            fingerprint=fingerprint,
            confidence=payload.get("confidence", 0.0),
            prediction_interval=payload.get("prediction_interval", {}),
            risk_snapshot_id=payload.get("snapshot_id")
        )
        
        try:
            db.add(new_alert)
            await db.commit()
            await db.refresh(new_alert)
            await cls._publish_alert_event("ALERT_CREATED", new_alert)
            # WS broadcast after successful commit
            await broadcast_ws_event(
                event_type=WSEventType.ALERT_CREATED,
                region_id=new_alert.region_id,
                severity=new_alert.severity,
                payload={
                    "alert_id": new_alert.id,
                    "severity": new_alert.severity,
                    "message": new_alert.message,
                    "confidence": new_alert.confidence,
                },
            )
            return new_alert
        except IntegrityError:
            await db.rollback()
            logger.warning(f"Duplicate alert suppressed for fingerprint {fingerprint}")
            return None
            
    @classmethod
    async def _attempt_resolution(cls, db: AsyncSession, region_id: int) -> Optional[Alert]:
        stmt = select(Alert).where(Alert.region_id == region_id, Alert.is_active == True)
        result = await db.execute(stmt)
        active_alert = result.scalars().first()
        
        if active_alert:
            active_alert.is_active = False
            active_alert.updated_at = datetime.now(timezone.utc)
            db.add(active_alert)
            await db.commit()
            await db.refresh(active_alert)
            await cls._publish_alert_event("ALERT_RESOLVED", active_alert)
            # WS broadcast after successful commit
            await broadcast_ws_event(
                event_type=WSEventType.ALERT_RESOLVED,
                region_id=active_alert.region_id,
                severity=active_alert.severity,
                payload={"alert_id": active_alert.id, "severity": active_alert.severity},
            )
            return active_alert
        return None
        
    @classmethod
    async def _publish_alert_event(cls, event_type: str, alert: Alert):
        payload = {
            "alert_id": alert.id,
            "region_id": alert.region_id,
            "severity": alert.severity,
            "message": alert.message,
            "confidence": alert.confidence,
            "prediction_interval": alert.prediction_interval,
            "risk_snapshot_id": alert.risk_snapshot_id,
            "timestamp": alert.updated_at.isoformat() if alert.updated_at else datetime.now(timezone.utc).isoformat()
        }
        await EventPublisher.publish_event(
            event_type=event_type,
            region_id=alert.region_id,
            source="AlertIntelligenceService",
            payload=payload
        )
