from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import timedelta
from app.realtime.event_schema import IntelligenceEvent
from app.cep.schemas import CEPPatternMatch
from app.cep.window import TemporalWindowEngine

class CEPPatternRule(ABC):
    rule_id: str
    name: str
    description: str
    enabled: bool = True
    priority: int = 1
    time_window: timedelta = timedelta(hours=24)
    spatial_radius: float = 0.0
    minimum_events: int = 2
    minimum_signal_diversity: int = 1
    cooldown: timedelta = timedelta(hours=1)

    @abstractmethod
    async def evaluate(self, event: IntelligenceEvent, context_events: List[IntelligenceEvent]) -> Optional[CEPPatternMatch]:
        """
        Evaluates the current event against historical context_events to find a pattern match.
        """
        pass

class RapidRiskEscalationRule(CEPPatternRule):
    rule_id = "RAPID_RISK_ESCALATION"
    name = "Rapid Risk Escalation"
    description = "Detects rapid regional risk increase within a short window."
    time_window = timedelta(hours=24)
    minimum_events = 2

    async def evaluate(self, event: IntelligenceEvent, context_events: List[IntelligenceEvent]) -> Optional[CEPPatternMatch]:
        if event.event_type != "RISK_CHANGED":
            return None
            
        recent_risk_events = [e for e in context_events if e.event_type == "RISK_CHANGED" and e.region_id == event.region_id]
        recent_risk_events.append(event)
        
        if len(recent_risk_events) < self.minimum_events:
            return None
            
        # Check if risk increased significantly
        scores = [e.payload.get("risk_score", 0) for e in recent_risk_events]
        if max(scores) - min(scores) > 0.15 and scores[-1] > scores[0]:
            return CEPPatternMatch(
                rule_id=self.rule_id,
                matched=True,
                score=0.8,
                confidence=0.8,
                event_ids=[e.event_id for e in recent_risk_events],
                region_ids=[event.region_id],
                evidence={"risk_delta": max(scores) - min(scores), "event_count": len(recent_risk_events)},
                spatial_context={"primary_region": event.region_id},
                temporal_context={"window_hours": 24},
                explanation="Multiple risk changes indicate rapid escalation."
            )
        return None

class EnvironmentalRiskConvergenceRule(CEPPatternRule):
    rule_id = "ENVIRONMENTAL_RISK_CONVERGENCE"
    name = "Environmental Risk Convergence"
    description = "Detects environmental signals correlating with risk changes."
    time_window = timedelta(hours=24)
    minimum_events = 2
    minimum_signal_diversity = 2

    async def evaluate(self, event: IntelligenceEvent, context_events: List[IntelligenceEvent]) -> Optional[CEPPatternMatch]:
        events = [e for e in context_events if e.region_id == event.region_id]
        events.append(event)
        
        types = set(e.event_type for e in events)
        if len(types) >= self.minimum_signal_diversity and "RISK_CHANGED" in types and ("RAINFALL_UPDATE" in types or "WATER_QUALITY_UPDATE" in types):
            return CEPPatternMatch(
                rule_id=self.rule_id,
                matched=True,
                score=0.7,
                confidence=0.75,
                event_ids=[e.event_id for e in events],
                region_ids=[event.region_id],
                evidence={"signal_types": list(types)},
                spatial_context={"primary_region": event.region_id},
                temporal_context={"window_hours": 24},
                explanation="Environmental signals converged with a risk escalation."
            )
        return None

class DiseaseMomentumRule(CEPPatternRule):
    rule_id = "DISEASE_MOMENTUM"
    name = "Disease Momentum"
    description = "Detects unusual regional disease-related signal momentum."
    time_window = timedelta(days=7)
    minimum_events = 3

    async def evaluate(self, event: IntelligenceEvent, context_events: List[IntelligenceEvent]) -> Optional[CEPPatternMatch]:
        if event.event_type != "DISEASE_CASE_UPDATE":
            return None
            
        disease_events = [e for e in context_events if e.event_type == "DISEASE_CASE_UPDATE" and e.region_id == event.region_id]
        disease_events.append(event)
        
        if len(disease_events) >= self.minimum_events:
            return CEPPatternMatch(
                rule_id=self.rule_id,
                matched=True,
                score=0.6,
                confidence=0.7,
                event_ids=[e.event_id for e in disease_events],
                region_ids=[event.region_id],
                evidence={"event_count": len(disease_events)},
                spatial_context={"primary_region": event.region_id},
                temporal_context={"window_days": 7},
                explanation="Sustained increase in synthetic aggregated disease-case signals."
            )
        return None

class SpatialCascadeRule(CEPPatternRule):
    rule_id = "SPATIAL_CASCADE"
    name = "Spatial Cascade"
    description = "Detects correlated events propagating across neighboring regions."
    time_window = timedelta(hours=48)
    minimum_events = 2

    async def evaluate(self, event: IntelligenceEvent, context_events: List[IntelligenceEvent]) -> Optional[CEPPatternMatch]:
        # For simplicity, we assume context_events already contains neighbor events
        risk_events = [e for e in context_events if e.event_type == "RISK_CHANGED"]
        risk_events.append(event)
        
        regions = set(e.region_id for e in risk_events)
        if len(regions) > 1 and event.event_type == "RISK_CHANGED":
            return CEPPatternMatch(
                rule_id=self.rule_id,
                matched=True,
                score=0.8,
                confidence=0.8,
                event_ids=[e.event_id for e in risk_events],
                region_ids=list(regions),
                evidence={"affected_regions_count": len(regions)},
                spatial_context={"regions": list(regions)},
                temporal_context={"window_hours": 48},
                explanation="Risk increase propagated across multiple connected regions."
            )
        return None

class MultiSignalAnomalyRule(CEPPatternRule):
    rule_id = "MULTI_SIGNAL_ANOMALY"
    name = "Multi-Signal Anomaly"
    description = "Detects multiple independent anomalous signals within a time window."
    time_window = timedelta(hours=24)
    minimum_events = 2

    async def evaluate(self, event: IntelligenceEvent, context_events: List[IntelligenceEvent]) -> Optional[CEPPatternMatch]:
        anomaly_events = [e for e in context_events if e.event_type == "ANOMALY_DETECTED" and e.region_id == event.region_id]
        if event.event_type == "ANOMALY_DETECTED":
            anomaly_events.append(event)
            
        if len(anomaly_events) >= self.minimum_events:
            return CEPPatternMatch(
                rule_id=self.rule_id,
                matched=True,
                score=0.75,
                confidence=0.8,
                event_ids=[e.event_id for e in anomaly_events],
                region_ids=[event.region_id],
                evidence={"anomaly_count": len(anomaly_events)},
                spatial_context={"primary_region": event.region_id},
                temporal_context={"window_hours": 24},
                explanation="Multiple distinct anomalies detected concurrently."
            )
        return None

class ModelDriftEscalationRule(CEPPatternRule):
    rule_id = "MODEL_DRIFT_ESCALATION"
    name = "Model Drift Escalation"
    description = "Detects worsening model/data drift combined with increasing risk uncertainty."
    time_window = timedelta(days=7)
    minimum_events = 3

    async def evaluate(self, event: IntelligenceEvent, context_events: List[IntelligenceEvent]) -> Optional[CEPPatternMatch]:
        drift_events = [e for e in context_events if e.event_type == "MODEL_DRIFT_DETECTED"]
        if event.event_type == "MODEL_DRIFT_DETECTED":
            drift_events.append(event)
            
        if len(drift_events) >= self.minimum_events:
            return CEPPatternMatch(
                rule_id=self.rule_id,
                matched=True,
                score=0.6,
                confidence=0.9,
                event_ids=[e.event_id for e in drift_events],
                region_ids=[],
                evidence={"drift_event_count": len(drift_events)},
                spatial_context={"system_wide": True},
                temporal_context={"window_days": 7},
                explanation="Repeated divergence metrics indicate escalating model drift."
            )
        return None

class CommunitySignalClusterRule(CEPPatternRule):
    rule_id = "COMMUNITY_SIGNAL_CLUSTER"
    name = "Community Signal Cluster"
    description = "Detects spatially and temporally clustered community reports."
    time_window = timedelta(hours=24)
    minimum_events = 3

    async def evaluate(self, event: IntelligenceEvent, context_events: List[IntelligenceEvent]) -> Optional[CEPPatternMatch]:
        reports = [e for e in context_events if e.event_type == "COMMUNITY_REPORT" and e.region_id == event.region_id]
        if event.event_type == "COMMUNITY_REPORT":
            reports.append(event)
            
        if len(reports) >= self.minimum_events:
            return CEPPatternMatch(
                rule_id=self.rule_id,
                matched=True,
                score=0.65,
                confidence=0.6,
                event_ids=[e.event_id for e in reports],
                region_ids=[event.region_id],
                evidence={"report_count": len(reports)},
                spatial_context={"primary_region": event.region_id},
                temporal_context={"window_hours": 24},
                explanation="Cluster of unverified community reports detected."
            )
        return None

class CompoundRiskEventRule(CEPPatternRule):
    rule_id = "COMPOUND_RISK_EVENT"
    name = "Compound Risk Event"
    description = "Combines multiple independent signal classes (Environmental, Anomaly, Risk, Community)."
    time_window = timedelta(hours=48)
    minimum_events = 4
    minimum_signal_diversity = 3

    async def evaluate(self, event: IntelligenceEvent, context_events: List[IntelligenceEvent]) -> Optional[CEPPatternMatch]:
        events = [e for e in context_events if e.region_id == event.region_id]
        events.append(event)
        
        types = set(e.event_type for e in events)
        
        if len(types) >= self.minimum_signal_diversity and len(events) >= self.minimum_events:
            return CEPPatternMatch(
                rule_id=self.rule_id,
                matched=True,
                score=0.9,
                confidence=0.95,
                event_ids=[e.event_id for e in events],
                region_ids=[event.region_id],
                evidence={"signal_types": list(types), "total_events": len(events)},
                spatial_context={"primary_region": event.region_id},
                temporal_context={"window_hours": 48},
                explanation="Multiple independent evidence sources (environmental, risk, anomaly, etc.) have converged."
            )
        return None
