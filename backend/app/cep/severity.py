from typing import List, Dict, Any
from app.models.domain import IncidentSeverity
from app.cep.schemas import CEPPatternMatch
from app.realtime.event_schema import IntelligenceEvent

class SeverityEngine:
    """
    Deterministic severity scoring.
    """
    
    @staticmethod
    def calculate_severity(
        match: CEPPatternMatch, 
        events: List[IntelligenceEvent]
    ) -> IncidentSeverity:
        score = 0.0
        
        # 1. Risk Component
        risk_events = [e for e in events if e.event_type == "RISK_CHANGED"]
        if risk_events:
            max_risk = max([e.payload.get("risk_score", 0.0) for e in risk_events])
            score += max_risk * 0.4
            
        # 2. Anomaly Component
        anomaly_events = [e for e in events if e.event_type == "ANOMALY_DETECTED"]
        if anomaly_events:
            score += min(len(anomaly_events) * 0.1, 0.2)
            
        # 3. Spatial Component
        if len(match.region_ids) > 1:
            score += min(len(match.region_ids) * 0.05, 0.2)
            
        # 4. Diversity Component
        types = set(e.event_type for e in events)
        score += min(len(types) * 0.05, 0.2)
        
        # Mapping Score to Enum
        if score >= 0.8:
            return IncidentSeverity.CRITICAL
        elif score >= 0.6:
            return IncidentSeverity.HIGH
        elif score >= 0.4:
            return IncidentSeverity.MEDIUM
        elif score >= 0.2:
            return IncidentSeverity.LOW
        else:
            return IncidentSeverity.INFO

class IncidentConfidenceEngine:
    """
    Determines confidence based on independent evidence sources and temporal consistency.
    """
    
    @staticmethod
    def calculate_confidence(
        match: CEPPatternMatch, 
        events: List[IntelligenceEvent]
    ) -> float:
        confidence = 0.5 # Base confidence
        
        # Number of independent signals
        types = set(e.event_type for e in events)
        if len(types) >= 3:
            confidence += 0.2
        elif len(types) == 2:
            confidence += 0.1
            
        # Rule agreement
        if match.score > 0.8:
            confidence += 0.1
            
        # Temporal density
        if len(events) >= 5:
            confidence += 0.1
            
        # Data Quality (Example: penalty for demo data)
        # Assuming Data Quality is inherently tracked, we simply add a placeholder cap.
        
        return min(1.0, confidence)
