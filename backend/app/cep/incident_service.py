import logging
import uuid
import json
from typing import List, Optional, Dict
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.domain import IntelligenceIncident, IncidentStatus, IncidentSeverity
from app.cep.schemas import IntelligenceIncidentCreate
from app.realtime.publisher import EventPublisher
from app.realtime.ws_broadcaster import broadcast_ws_event
from app.realtime.ws_events import WSEventType
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

class IncidentService:
    """
    CRUD operations and lifecycle management for IntelligenceIncidents.
    """

    @staticmethod
    async def create_incident(db: AsyncSession, incident_in: IntelligenceIncidentCreate) -> IntelligenceIncident:
        incident_id = str(uuid.uuid4())
        
        incident = IntelligenceIncident(
            incident_id=incident_id,
            incident_type=incident_in.incident_type,
            title=incident_in.title,
            description=incident_in.description,
            region_id=incident_in.region_id,
            severity=incident_in.severity,
            confidence=incident_in.confidence,
            status=IncidentStatus.OPEN,
            first_detected_at=incident_in.first_detected_at,
            last_updated_at=incident_in.last_updated_at,
            correlation_id=incident_in.correlation_id,
            event_count=len(incident_in.source_event_ids),
            source_event_ids=incident_in.source_event_ids,
            triggered_rules=incident_in.triggered_rules,
            evidence=incident_in.evidence,
            spatial_context=incident_in.spatial_context,
            temporal_context=incident_in.temporal_context,
            risk_before=incident_in.risk_before,
            risk_after=incident_in.risk_after,
            risk_delta=incident_in.risk_delta,
            signal_diversity=incident_in.signal_diversity
        )
        
        db.add(incident)
        await db.commit()
        await db.refresh(incident)
        
        # Publish to Redis Streams (durable processing)
        await EventPublisher.publish_event(
            event_type="INTELLIGENCE_INCIDENT_CREATED",
            region_id=incident.region_id,
            source="cep_engine",
            payload={"incident_id": incident.incident_id, "severity": incident.severity, "type": incident.incident_type},
            correlation_id=incident.correlation_id
        )
        # WS broadcast (transient, after commit)
        await broadcast_ws_event(
            event_type=WSEventType.INTELLIGENCE_INCIDENT_CREATED,
            region_id=incident.region_id,
            severity=str(incident.severity),
            correlation_id=incident.correlation_id,
            payload={
                "incident_id": incident.incident_id,
                "title": incident.title,
                "severity": str(incident.severity),
                "incident_type": incident.incident_type,
                "confidence": incident.confidence,
            },
        )
        return incident

    @staticmethod
    async def update_incident(
        db: AsyncSession, 
        incident_id: str, 
        new_event_ids: List[str], 
        new_rules: List[str], 
        new_confidence: float,
        new_evidence: Optional[Dict] = None,
        risk_before: Optional[float] = None,
        risk_after: Optional[float] = None,
        risk_delta: Optional[float] = None
    ) -> IntelligenceIncident:
        
        stmt = select(IntelligenceIncident).where(IntelligenceIncident.incident_id == incident_id)
        result = await db.execute(stmt)
        incident = result.scalar_one_or_none()
        
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")
            
        # Update event IDs uniquely
        combined_events = list(set(incident.source_event_ids + new_event_ids))
        combined_rules = list(set(incident.triggered_rules + new_rules))
        
        incident.source_event_ids = combined_events
        incident.event_count = len(combined_events)
        incident.triggered_rules = combined_rules
        incident.last_updated_at = datetime.now(timezone.utc)
        
        if new_evidence:
            current_evidence = incident.evidence or {}
            # Merge evidence, keeping new values or appending to lists
            for k, v in new_evidence.items():
                if isinstance(v, list) and isinstance(current_evidence.get(k), list):
                    current_evidence[k] = list(set(current_evidence[k] + v))
                else:
                    current_evidence[k] = v
            incident.evidence = current_evidence
            
        if risk_before is not None:
            incident.risk_before = risk_before
        if risk_after is not None:
            incident.risk_after = risk_after
        if risk_delta is not None:
            incident.risk_delta = risk_delta
        
        # Severity is inherited from the original incident creation.
        # It is not escalated on update since the caller determines severity at creation time.
            
        incident.confidence = max(incident.confidence, new_confidence)
        
        await db.commit()
        await db.refresh(incident)
        
        await EventPublisher.publish_event(
            event_type="INTELLIGENCE_INCIDENT_UPDATED",
            region_id=incident.region_id,
            source="cep_engine",
            payload={"incident_id": incident.incident_id, "severity": incident.severity.value, "type": incident.incident_type},
            correlation_id=incident.correlation_id
        )
        # WS broadcast (transient, after commit)
        await broadcast_ws_event(
            event_type=WSEventType.INTELLIGENCE_INCIDENT_UPDATED,
            region_id=incident.region_id,
            severity=incident.severity.value,
            correlation_id=incident.correlation_id,
            payload={
                "incident_id": incident.incident_id,
                "severity": incident.severity.value,
                "confidence": incident.confidence,
                "event_count": incident.event_count,
            },
        )
        return incident

    @staticmethod
    async def transition_status(db: AsyncSession, incident_id: str, new_status: IncidentStatus) -> IntelligenceIncident:
        stmt = select(IntelligenceIncident).where(IntelligenceIncident.incident_id == incident_id)
        result = await db.execute(stmt)
        incident = result.scalar_one_or_none()
        
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")
            
        # Validate transition
        valid_transitions = {
            IncidentStatus.OPEN: [IncidentStatus.INVESTIGATING, IncidentStatus.RESOLVED],
            IncidentStatus.INVESTIGATING: [IncidentStatus.ESCALATED, IncidentStatus.RESOLVED],
            IncidentStatus.ESCALATED: [IncidentStatus.RESOLVED],
            IncidentStatus.RESOLVED: [IncidentStatus.INVESTIGATING] # Reopen
        }
        
        if new_status not in valid_transitions.get(incident.status, []):
            raise ValueError(f"Invalid state transition from {incident.status} to {new_status}")
            
        incident.status = new_status
        if new_status == IncidentStatus.RESOLVED:
            incident.resolved_at = datetime.now(timezone.utc)
            
        await db.commit()
        await db.refresh(incident)
        
        event_type = f"INTELLIGENCE_INCIDENT_{new_status.value}"
        await EventPublisher.publish_event(
            event_type=event_type,
            region_id=incident.region_id,
            source="cep_engine",
            payload={"incident_id": incident.incident_id, "status": new_status.value},
            correlation_id=incident.correlation_id
        )
        # WS broadcast (transient, after commit)
        ws_event = (
            WSEventType.INTELLIGENCE_INCIDENT_RESOLVED
            if new_status == IncidentStatus.RESOLVED
            else WSEventType.INTELLIGENCE_INCIDENT_ESCALATED
            if new_status == IncidentStatus.ESCALATED
            else WSEventType.INTELLIGENCE_INCIDENT_UPDATED
        )
        await broadcast_ws_event(
            event_type=ws_event,
            region_id=incident.region_id,
            severity=incident.severity.value,
            correlation_id=incident.correlation_id,
            payload={"incident_id": incident.incident_id, "status": new_status.value},
        )
        return incident
