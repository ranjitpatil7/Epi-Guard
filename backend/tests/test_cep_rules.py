import pytest
from datetime import datetime, timezone, timedelta
import uuid
from app.realtime.event_schema import IntelligenceEvent
from app.cep.rules import (
    RapidRiskEscalationRule, EnvironmentalRiskConvergenceRule,
    DiseaseMomentumRule, SpatialCascadeRule, MultiSignalAnomalyRule,
    ModelDriftEscalationRule, CommunitySignalClusterRule, CompoundRiskEventRule
)

def _make_event(event_type, payload, region_id=1, dt=None):
    if dt is None:
        dt = datetime.now(timezone.utc)
    return IntelligenceEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        region_id=region_id,
        source="test",
        timestamp=dt,
        payload=payload,
        correlation_id=str(uuid.uuid4())
    )

@pytest.mark.asyncio
async def test_rapid_risk_escalation():
    rule = RapidRiskEscalationRule()
    dt = datetime.now(timezone.utc)
    
    # Positive
    context = [
        _make_event("RISK_CHANGED", {"risk_score": 0.5, "risk_delta": 0.05}, dt=dt - timedelta(hours=2))
    ]
    trigger = _make_event("RISK_CHANGED", {"risk_score": 0.85, "risk_delta": 0.35}, dt=dt)
    
    match = await rule.evaluate(trigger, context)
    assert match is not None
    assert match.matched is True
    
    # Negative
    trigger_neg = _make_event("RISK_CHANGED", {"risk_score": 0.6, "risk_delta": 0.1}, dt=dt)
    match_neg = await rule.evaluate(trigger_neg, context)
    assert match_neg is None

@pytest.mark.asyncio
async def test_environmental_risk_convergence():
    rule = EnvironmentalRiskConvergenceRule()
    dt = datetime.now(timezone.utc)
    
    context = [
        _make_event("RAINFALL_UPDATE", {"rainfall": 120.0}, dt=dt - timedelta(hours=1)),
        _make_event("WATER_QUALITY_UPDATE", {"wqi": 35.0}, dt=dt - timedelta(minutes=30))
    ]
    trigger = _make_event("RISK_CHANGED", {"risk_score": 0.75, "risk_delta": 0.25}, dt=dt)
    
    match = await rule.evaluate(trigger, context)
    assert match is not None
    assert match.matched is True

@pytest.mark.asyncio
async def test_disease_momentum():
    rule = DiseaseMomentumRule()
    dt = datetime.now(timezone.utc)
    
    context = [
        _make_event("DISEASE_CASE_UPDATE", {"disease_signal": True}, dt=dt - timedelta(days=1)),
        _make_event("DISEASE_CASE_UPDATE", {"disease_signal": True}, dt=dt - timedelta(hours=12))
    ]
    trigger = _make_event("DISEASE_CASE_UPDATE", {"disease_signal": True}, dt=dt)
    
    match = await rule.evaluate(trigger, context)
    assert match is not None
    assert match.matched is True

@pytest.mark.asyncio
async def test_spatial_cascade():
    rule = SpatialCascadeRule()
    dt = datetime.now(timezone.utc)
    
    context = [
        _make_event("RISK_CHANGED", {"risk_score": 0.9}, region_id=2, dt=dt - timedelta(hours=2)),
        _make_event("RISK_CHANGED", {"risk_score": 0.85}, region_id=3, dt=dt - timedelta(hours=1))
    ]
    trigger = _make_event("RISK_CHANGED", {"risk_score": 0.88}, region_id=1, dt=dt)
    
    match = await rule.evaluate(trigger, context)
    assert match is not None
    assert match.matched is True

@pytest.mark.asyncio
async def test_multi_signal_anomaly():
    rule = MultiSignalAnomalyRule()
    dt = datetime.now(timezone.utc)
    
    context = [
        _make_event("ANOMALY_DETECTED", {"anomaly_score": 0.9}, dt=dt - timedelta(hours=1))
    ]
    trigger = _make_event("ANOMALY_DETECTED", {"anomaly_score": 0.85}, dt=dt)
    
    match = await rule.evaluate(trigger, context)
    assert match is not None
    assert match.matched is True

@pytest.mark.asyncio
async def test_model_drift_escalation():
    rule = ModelDriftEscalationRule()
    dt = datetime.now(timezone.utc)
    
    context = [
        _make_event("MODEL_DRIFT_DETECTED", {"psi_score": 0.3}, dt=dt - timedelta(hours=2)),
        _make_event("MODEL_DRIFT_DETECTED", {"psi_score": 0.35}, dt=dt - timedelta(hours=1))
    ]
    trigger = _make_event("MODEL_DRIFT_DETECTED", {"psi_score": 0.4}, dt=dt)
    
    match = await rule.evaluate(trigger, context)
    assert match is not None
    assert match.matched is True

@pytest.mark.asyncio
async def test_community_signal_cluster():
    rule = CommunitySignalClusterRule()
    dt = datetime.now(timezone.utc)
    
    context = [
        _make_event("COMMUNITY_REPORT", {"severity": "HIGH"}, dt=dt - timedelta(hours=2)),
        _make_event("COMMUNITY_REPORT", {"severity": "HIGH"}, dt=dt - timedelta(hours=1)),
        _make_event("COMMUNITY_REPORT", {"severity": "HIGH"}, dt=dt - timedelta(minutes=30))
    ]
    trigger = _make_event("COMMUNITY_REPORT", {"severity": "HIGH"}, dt=dt)
    
    match = await rule.evaluate(trigger, context)
    assert match is not None
    assert match.matched is True

@pytest.mark.asyncio
async def test_compound_risk_event():
    rule = CompoundRiskEventRule()
    dt = datetime.now(timezone.utc)
    
    context = [
        _make_event("RAINFALL_UPDATE", {"rainfall": 150.0}, dt=dt - timedelta(hours=3)),
        _make_event("WATER_QUALITY_UPDATE", {"wqi": 30.0}, dt=dt - timedelta(hours=2)),
        _make_event("ANOMALY_DETECTED", {"anomaly_score": 0.95}, dt=dt - timedelta(hours=1))
    ]
    trigger = _make_event("RISK_CHANGED", {"risk_score": 0.85, "risk_delta": 0.3}, dt=dt)
    
    match = await rule.evaluate(trigger, context)
    assert match is not None
    assert match.matched is True
