with open("tests/test_cep_engine.py", "w", encoding="utf-8") as f:
    f.write("""import pytest
from datetime import datetime, timezone
import uuid
from unittest.mock import patch, AsyncMock
from app.realtime.event_schema import IntelligenceEvent
from app.cep.engine import CEPEngine

@pytest.mark.asyncio
async def test_cep_demo_mode_compound_risk():
    engine = CEPEngine()
    base_time = datetime.now(timezone.utc)
    region_id = 1
    events = [
        IntelligenceEvent(
            event_id=f"demo-env-{uuid.uuid4()}",
            event_type="RAINFALL_UPDATE",
            region_id=region_id,
            source="demo_system",
            timestamp=base_time,
            payload={"rainfall": 150.0},
            correlation_id="demo-correlation"
        ),
        IntelligenceEvent(
            event_id=f"demo-wq-{uuid.uuid4()}",
            event_type="WATER_QUALITY_UPDATE",
            region_id=region_id,
            source="demo_system",
            timestamp=base_time,
            payload={"wqi": 30.0},
            correlation_id="demo-correlation"
        ),
        IntelligenceEvent(
            event_id=f"demo-anom-{uuid.uuid4()}",
            event_type="ANOMALY_DETECTED",
            region_id=region_id,
            source="demo_system",
            timestamp=base_time,
            payload={"anomaly_score": 0.95},
            correlation_id="demo-correlation"
        ),
    ]
    from app.cep.rules import CompoundRiskEventRule
    rule = CompoundRiskEventRule()
    trigger_event = IntelligenceEvent(
        event_id=f"demo-risk-{uuid.uuid4()}",
        event_type="RISK_CHANGED",
        region_id=region_id,
        source="demo_system",
        timestamp=base_time,
        payload={"risk_score": 0.85, "risk_delta": 0.3},
        correlation_id="demo-correlation"
    )
    match = await rule.evaluate(trigger_event, events)
    assert match is not None
    assert match.matched is True
    assert match.rule_id == "COMPOUND_RISK_EVENT"
    assert len(match.event_ids) == 4
    assert match.region_ids == [1]

@pytest.mark.asyncio
async def test_cep_ignores_incident_events():
    engine = CEPEngine()
    with patch("app.cep.engine.AsyncSessionLocal") as mock_db:
        event_created = IntelligenceEvent(
            event_id=f"test-{uuid.uuid4()}",
            event_type="INTELLIGENCE_INCIDENT_CREATED",
            region_id=1,
            source="cep",
            timestamp=datetime.now(timezone.utc),
            payload={},
            correlation_id="test"
        )
        event_updated = IntelligenceEvent(
            event_id=f"test-{uuid.uuid4()}",
            event_type="INTELLIGENCE_INCIDENT_UPDATED",
            region_id=1,
            source="cep",
            timestamp=datetime.now(timezone.utc),
            payload={},
            correlation_id="test"
        )
        await engine.process_incoming_event(event_created)
        await engine.process_incoming_event(event_updated)
        mock_db.assert_not_called()
""")
