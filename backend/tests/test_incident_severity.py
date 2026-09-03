import pytest
from app.cep.severity import SeverityEngine
from app.models.domain import IncidentSeverity
from app.cep.rules import CEPPatternMatch
from app.realtime.event_schema import IntelligenceEvent
from datetime import datetime, timezone
import uuid

def test_severity_calculation():
    match_high = CEPPatternMatch(
        matched=True,
        rule_id="COMPOUND_RISK_EVENT",
        score=0.9,
        confidence=0.9,
        event_ids=[str(uuid.uuid4()) for _ in range(4)],
        region_ids=[1, 2],
        explanation="",
        evidence={"risk_delta": 0.35, "anomaly_max": 0.9},
        spatial_context={},
        temporal_context={}
    )
    
    dt = datetime.now(timezone.utc)
    events = [
        IntelligenceEvent(event_id="1", event_type="RISK_CHANGED", region_id=1, source="test", timestamp=dt, payload={"risk_score": 0.95}, correlation_id="c1"),
        IntelligenceEvent(event_id="2", event_type="ANOMALY_DETECTED", region_id=1, source="test", timestamp=dt, payload={}, correlation_id="c1"),
        IntelligenceEvent(event_id="3", event_type="ANOMALY_DETECTED", region_id=1, source="test", timestamp=dt, payload={}, correlation_id="c1"),
        IntelligenceEvent(event_id="4", event_type="RAINFALL_UPDATE", region_id=1, source="test", timestamp=dt, payload={}, correlation_id="c1")
    ]
    
    sev = SeverityEngine.calculate_severity(match_high, events)
    # 0.95 * 0.4 = 0.38
    # 2 anomalies * 0.1 = 0.2
    # 2 regions * 0.05 = 0.1
    # 3 types (RISK, ANOMALY, RAINFALL) * 0.05 = 0.15
    # Total = 0.38 + 0.2 + 0.1 + 0.15 = 0.83
    assert sev == IncidentSeverity.CRITICAL
    
    match_low = CEPPatternMatch(
        matched=True,
        rule_id="COMPOUND_RISK_EVENT",
        score=0.9,
        confidence=0.9,
        event_ids=[str(uuid.uuid4())],
        region_ids=[1],
        explanation="",
        evidence={"risk_delta": 0.05},
        spatial_context={},
        temporal_context={}
    )
    
    sev_low = SeverityEngine.calculate_severity(match_low, [])
    assert sev_low == IncidentSeverity.INFO
