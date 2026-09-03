import pytest
from app.cep.severity import IncidentConfidenceEngine
from app.cep.rules import CEPPatternMatch
from app.realtime.event_schema import IntelligenceEvent
from datetime import datetime, timezone

def test_confidence_calculation():
    # Confidence is determined by number of independent events and their individual confidence
    match = CEPPatternMatch(
        matched=True,
        rule_id="TEST",
        score=0.9,
        confidence=0.9,
        event_ids=["1", "2"],
        region_ids=[1],
        explanation="",
        evidence={},
        spatial_context={},
        temporal_context={}
    )
    
    dt = datetime.now(timezone.utc)
    events = [
        IntelligenceEvent(event_id="1", event_type="E1", region_id=1, source="s1", timestamp=dt, payload={}, correlation_id="c1", confidence=0.8),
        IntelligenceEvent(event_id="2", event_type="E2", region_id=1, source="s2", timestamp=dt, payload={}, correlation_id="c1", confidence=0.9),
        IntelligenceEvent(event_id="3", event_type="E3", region_id=1, source="s3", timestamp=dt, payload={}, correlation_id="c1", confidence=0.9),
        IntelligenceEvent(event_id="4", event_type="E3", region_id=1, source="s3", timestamp=dt, payload={}, correlation_id="c1", confidence=0.9),
        IntelligenceEvent(event_id="5", event_type="E3", region_id=1, source="s3", timestamp=dt, payload={}, correlation_id="c1", confidence=0.9)
    ]
    
    conf = IncidentConfidenceEngine.calculate_confidence(match, events)
    
    # 0.5 base + 0.2 (3 signal types) + 0.1 (score > 0.8) + 0.1 (5+ events) = 0.9
    assert conf > 0.8
    assert conf <= 1.0
    
    # Check that Risk != Confidence (risk is a payload metric, confidence evaluates signal quality)
    assert conf != 0.8 # It's an aggregation
