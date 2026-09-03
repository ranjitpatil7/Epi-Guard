import logging
from typing import List, Optional
from datetime import timedelta, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.domain import IntelligenceEvent as DBIntelligenceEvent
from app.realtime.event_schema import IntelligenceEvent
from app.cep.window import TemporalWindowEngine
from app.cep.rules import (
    RapidRiskEscalationRule, EnvironmentalRiskConvergenceRule, 
    DiseaseMomentumRule, SpatialCascadeRule, MultiSignalAnomalyRule, 
    ModelDriftEscalationRule, CommunitySignalClusterRule, CompoundRiskEventRule
)
from app.cep.correlator import IncidentCorrelator
from app.cep.severity import SeverityEngine, IncidentConfidenceEngine
from app.cep.deduplication import IncidentDeduplicator
from app.cep.incident_service import IncidentService
from app.cep.schemas import IntelligenceIncidentCreate
from app.db.session import AsyncSessionLocal
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class CEPEngine:
    """
    Main orchestrator for Complex Event Processing.
    """
    
    def __init__(self):
        self.rules = [
            CompoundRiskEventRule(),
            RapidRiskEscalationRule(),
            EnvironmentalRiskConvergenceRule(),
            SpatialCascadeRule(),
            MultiSignalAnomalyRule(),
            CommunitySignalClusterRule(),
            DiseaseMomentumRule(),
            ModelDriftEscalationRule()
        ]
        
    async def process_incoming_event(self, event: IntelligenceEvent):
        """
        Main entrypoint from the Redis Subscriber.
        """
        # P0 Fix: Ignore internal incident notification events to prevent infinite CEP loops
        if event.event_type and event.event_type.startswith("INTELLIGENCE_INCIDENT"):
            logger.info(f"CEPEngine ignoring internal incident event {event.event_id} ({event.event_type})")
            return
            
        logger.info(f"CEPEngine evaluating event {event.event_id}")
        
        async with AsyncSessionLocal() as db:
            # 1. Fetch recent events for temporal window (max 7 days to cover all rules)
            start_time = event.timestamp - timedelta(days=7)
            stmt = select(DBIntelligenceEvent).where(
                DBIntelligenceEvent.timestamp >= start_time,
                DBIntelligenceEvent.timestamp <= event.timestamp
            ).order_by(DBIntelligenceEvent.timestamp.asc())
            
            result = await db.execute(stmt)
            db_events = result.scalars().all()
            
            # Convert to Pydantic models for easier processing
            context_events = []
            for db_e in db_events:
                # We skip the current event if it's already in the DB to avoid duplication in rules
                if db_e.event_id != event.event_id:
                    context_events.append(IntelligenceEvent(
                        event_id=db_e.event_id,
                        event_type=db_e.event_type,
                        region_id=db_e.region_id,
                        source=db_e.source,
                        timestamp=db_e.timestamp,
                        payload=db_e.payload,
                        schema_version=db_e.schema_version,
                        confidence=db_e.confidence,
                        correlation_id=db_e.correlation_id
                    ))
                    
            # 2. Evaluate rules (highest priority first, based on array order)
            for rule in self.rules:
                if not rule.enabled:
                    continue
                    
                # Filter context events to the specific rule's time window
                rule_context = TemporalWindowEngine.get_events_in_window(context_events, rule.time_window, event.timestamp)
                
                match = await rule.evaluate(event, rule_context)
                if match and match.matched:
                    logger.info(f"CEPEngine matched pattern: {match.rule_id} for event {event.event_id}")
                    await self._handle_pattern_match(db, match, event, rule_context)
                    # We break on the first match to prevent generating multiple overlapping incidents 
                    # from the same event, unless we want overlapping incidents. (We'll break for simplicity/cleanliness).
                    break
                    
    async def _handle_pattern_match(self, db: AsyncSession, match: 'CEPPatternMatch', trigger_event: IntelligenceEvent, context_events: List[IntelligenceEvent]):
        """
        Process a successful pattern match: Correlate, Deduplicate, Create/Update Incident.
        """
        # All events involved in this match
        matched_events = [e for e in context_events if e.event_id in match.event_ids]
        if trigger_event.event_id in match.event_ids and trigger_event not in matched_events:
            matched_events.append(trigger_event)
            
        severity = SeverityEngine.calculate_severity(match, matched_events)
        confidence = IncidentConfidenceEngine.calculate_confidence(match, matched_events)
        
        # Determine deduplication fingerprint bucket
        time_bucket = IncidentDeduplicator.get_time_bucket(trigger_event.timestamp, bucket_hours=6)
        
        # Check for related existing incidents
        related_incidents = await IncidentCorrelator.find_related_incidents(db, match.region_ids, match.rule_id)
        
        # If we have an existing incident that is a strong correlation, we update it
        target_incident = None
        for inc in related_incidents:
            # Check if it's the exact same bucket fingerprint
            if IncidentDeduplicator.generate_fingerprint(match.rule_id, match.region_ids[0] if match.region_ids else 0, time_bucket) == IncidentDeduplicator.generate_fingerprint(inc.incident_type, inc.region_id, IncidentDeduplicator.get_time_bucket(inc.first_detected_at, 6)):
                target_incident = inc
                break
                
            # Otherwise use the correlator score
            score, reason = IncidentCorrelator.calculate_correlation_score(trigger_event, inc)
            if score > 0.5:
                target_incident = inc
                break
                
        if target_incident:
            # Update
            logger.info(f"Updating existing incident {target_incident.incident_id} with new event {trigger_event.event_id}")
            # Ensure we don't duplicate events in the array
            new_events = [e_id for e_id in match.event_ids if e_id not in target_incident.source_event_ids]
            if new_events:
                await IncidentService.update_incident(
                    db,
                    incident_id=target_incident.incident_id,
                    new_event_ids=new_events,
                    new_rules=[match.rule_id],
                    new_confidence=confidence,
                    new_evidence=match.evidence,
                    risk_delta=match.evidence.get("risk_delta")
                )
        else:
            # Create
            logger.info(f"Creating new incident {match.rule_id} triggered by {trigger_event.event_id}")
            creation_schema = IntelligenceIncidentCreate(
                incident_type=match.rule_id,
                title=f"{match.rule_id.replace('_', ' ').title()}",
                description=match.explanation,
                region_id=match.region_ids[0] if match.region_ids else trigger_event.region_id,
                severity=severity,
                confidence=confidence,
                correlation_id=trigger_event.correlation_id,
                source_event_ids=match.event_ids,
                triggered_rules=[match.rule_id],
                evidence=match.evidence,
                spatial_context=match.spatial_context,
                temporal_context=match.temporal_context,
                risk_delta=match.evidence.get("risk_delta"),
                signal_diversity=len(set(e.event_type for e in matched_events)),
                first_detected_at=min(e.timestamp for e in matched_events),
                last_updated_at=trigger_event.timestamp
            )
            await IncidentService.create_incident(db, creation_schema)
            
            # Phase 8: Trigger Escalation Matrix for CRITICAL incidents
            sev_val = severity.value if hasattr(severity, 'value') else severity
            if sev_val == "CRITICAL":
                await NotificationService.dispatch_critical_alert(
                    db,
                    region_id=creation_schema.region_id,
                    message=f"CRITICAL HEALTH ALERT: {creation_schema.title}. {creation_schema.description}"
                )
