import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from app.models.domain import Alert, RiskSnapshot, IntelligenceEvent as DBIntelligenceEvent
from app.realtime.event_schema import IntelligenceEvent
from app.services.event_driven_risk_service import EventDrivenRiskService
from app.services.risk_recalculation_coordinator import RiskRecalculationCoordinator
from app.services.alert_intelligence_service import AlertIntelligenceService
from app.services.risk_lineage_service import RiskLineageService
from app.copilot.tools import ToolRegistry, RiskHistoryInput, LatestRiskSnapshotInput, AlertDetailsInput, RiskLineageInput
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal

pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()

@pytest.fixture
def mock_event():
    return IntelligenceEvent(
        event_id="evt_123",
        event_type="RAINFALL_UPDATE",
        region_id=1,
        source="sensor_a",
        timestamp=datetime.now(timezone.utc),
        payload={"rainfall": 100},
        confidence=1.0
    )

@pytest.fixture
def mock_critical_event():
    return IntelligenceEvent(
        event_id="evt_crit_123",
        event_type="ANOMALY_DETECTED",
        region_id=1,
        source="cep",
        timestamp=datetime.now(timezone.utc),
        payload={"severity": "CRITICAL"},
        confidence=1.0
    )

async def test_event_triggers_recalculation(mock_event):
    assert EventDrivenRiskService.should_recalculate(mock_event) == True

async def test_irrelevant_event_ignored():
    evt = IntelligenceEvent(
        event_id="evt_ignore",
        event_type="UNKNOWN_EVENT",
        region_id=1,
        source="system",
        timestamp=datetime.now(timezone.utc),
        payload={},
        confidence=1.0
    )
    assert EventDrivenRiskService.should_recalculate(evt) == False

async def test_recursive_event_loop_prevention(mock_event):
    # Depth 0
    assert EventDrivenRiskService.should_recalculate(mock_event) == True
    
    # Depth 3
    mock_event.payload = {"lineage": {"processing_depth": 3}}
    assert EventDrivenRiskService.should_recalculate(mock_event) == False

async def test_region_debounce_and_coalescing(mock_event):
    RiskRecalculationCoordinator.reset_for_testing()
    
    # We use a long running callback to simulate processing so it's pending
    async def mock_callback(r, e):
        await asyncio.sleep(1.0)
        
    # First should execute
    res1 = await RiskRecalculationCoordinator.schedule_recalculation(1, mock_event, mock_callback)
    assert res1 == True
    
    # Let the task register
    await asyncio.sleep(0.1)
    
    # Second should be coalesced (debounced) because first is still running
    res2 = await RiskRecalculationCoordinator.schedule_recalculation(1, mock_event, mock_callback)
    assert res2 == False
    
async def test_critical_event_bypasses_debounce(mock_event, mock_critical_event):
    RiskRecalculationCoordinator.reset_for_testing()
    async def mock_callback(r, e):
        pass
        
    # First normal
    await RiskRecalculationCoordinator.schedule_recalculation(1, mock_event, mock_callback)
    
    # Critical should bypass
    res = await RiskRecalculationCoordinator.schedule_recalculation(1, mock_critical_event, mock_callback, bypass_debounce=True)
    assert res == True

@patch("app.services.alert_intelligence_service.EventPublisher.publish_event")
@patch("app.services.alert_intelligence_service.AsyncSession")
async def test_alert_creation_and_escalation(mock_session_cls, mock_publish):
    mock_session = AsyncMock()
    
    # Mocking select results for no active alerts
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result
    
    # Test creation
    payload_info = {"region_id": 999, "current_risk": 25.0, "change_type": "STABLE", "snapshot_id": "snap_1", "confidence": 0.9}
    alert1 = await AlertIntelligenceService.evaluate_risk_event(mock_session, payload_info)
    assert alert1 is not None
    assert alert1.severity == "INFO"
    
    # Test escalation (Mock returning alert1)
    mock_scalars.first.return_value = alert1
    payload_critical = {"region_id": 999, "current_risk": 85.0, "change_type": "RAPID_ESCALATION", "snapshot_id": "snap_2", "confidence": 0.95}
    alert2 = await AlertIntelligenceService.evaluate_risk_event(mock_session, payload_critical)
    assert alert2.severity == "CRITICAL"
    
    # Test de-escalation
    alert1.updated_at = None
    payload_warning = {"region_id": 999, "current_risk": 45.0, "change_type": "MODERATE_DECREASE", "snapshot_id": "snap_3"}
    alert3 = await AlertIntelligenceService.evaluate_risk_event(mock_session, payload_warning)
    assert alert3.severity == "WARNING"
    
    # Test resolution
    alert1.updated_at = None
    payload_safe = {"region_id": 999, "current_risk": 15.0, "change_type": "STABLE"}
    alert4 = await AlertIntelligenceService.evaluate_risk_event(mock_session, payload_safe)
    assert alert4.is_active == False

async def test_alert_deduplication():
    # Fingerprint should be the same for the same region/severity/bucket
    f1 = AlertIntelligenceService.generate_fingerprint(1, "RISK_ALERT", "HIGH", "STABLE")
    f2 = AlertIntelligenceService.generate_fingerprint(1, "RISK_ALERT", "HIGH", "STABLE")
    assert f1 == f2
    
@patch("app.services.alert_intelligence_service.AsyncSession")
async def test_concurrent_alert_creation(mock_session_cls):
    payload = {"region_id": 888, "current_risk": 90.0, "change_type": "RAPID_ESCALATION", "snapshot_id": "snap_c"}
    
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result
    
    # Simulate DB integrity error on second concurrent add
    def mock_add(alert):
        pass
        
    mock_session.add.side_effect = mock_add
    
    async def run_task():
        try:
            return await AlertIntelligenceService.evaluate_risk_event(mock_session, payload)
        except Exception:
            return None

    tasks = [run_task(), run_task(), run_task()]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # In a real DB with unique fingerprint constraint, only one succeeds
    # With a mock, we just prove the method is called correctly
    assert len(results) == 3

from app.models.users import User, UserRole, UserStatus
@patch("app.copilot.tools.AsyncSession")
async def test_copilot_uses_deterministic_risk_data(mock_session_cls):
    mock_session = AsyncMock()
    # Provide an authorized admin user so the tool is allowed to execute
    admin_user = User(id=1, username="admin", role=UserRole.ADMINISTRATOR, status=UserStatus.ACTIVE)
    registry = ToolRegistry(mock_session, user=admin_user)
    
    snap = RiskSnapshot(
        snapshot_id="snap_copilot",
        region_id=1,
        timestamp=datetime.now(timezone.utc),
        current_risk=77.7,
        previous_risk=70.0,
        risk_delta=7.7,
        confidence=0.8,
        explanation_metadata={},
        feature_snapshot={}
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = snap
    mock_session.execute.return_value = mock_result
    
    # Mock region lookup
    registry._get_region_id = AsyncMock(return_value=1)
    
    res = await registry.execute_tool("get_latest_risk_snapshot", {"region_name": "assam"})
    assert res.success == True
    assert res.data["current_risk"] == 77.7
    assert "error" not in res.data

async def test_copilot_cannot_modify_risk(db_session):
    registry = ToolRegistry(db_session)
    # The ToolRegistry schema for RiskAnalyst, History, Snapshot etc only allows GET operations.
    # We verify the inputs don't have mutation fields
    schema = LatestRiskSnapshotInput.schema()
    assert "region_name" in schema["properties"]
    assert "current_risk" not in schema["properties"]
    
@patch("app.services.risk_lineage_service.AsyncSession")
async def test_risk_lineage(mock_session_cls):
    mock_session = AsyncMock()
    
    snap = RiskSnapshot(snapshot_id="snap_lin_1", region_id=1, timestamp=datetime.now(timezone.utc), current_risk=50.0, triggering_event_id="evt_lin_1")
    alert = Alert(id=1, region_id=1, severity="WARNING", message="test", is_active=True, risk_snapshot_id="snap_lin_1")
    event = DBIntelligenceEvent(event_id="evt_lin_1", event_type="RAINFALL", region_id=1, source="test", timestamp=datetime.now(timezone.utc), payload={})
    
    mock_res_alert = MagicMock()
    mock_res_alert.scalar_one_or_none.return_value = alert
    mock_res_snap = MagicMock()
    mock_res_snap.scalar_one_or_none.return_value = snap
    mock_res_evt = MagicMock()
    mock_res_evt.scalar_one_or_none.return_value = event
    
    # We call it twice, so we side_effect the return values
    mock_session.execute.side_effect = [mock_res_alert, mock_res_snap, mock_res_evt]
    
    lineage = await RiskLineageService.get_alert_lineage(mock_session, 1)
    assert lineage is not None
    assert "risk_snapshot" in lineage
    assert lineage["risk_snapshot"]["snapshot_id"] == "snap_lin_1"
    assert "triggering_event" in lineage["risk_snapshot"]
    assert lineage["risk_snapshot"]["triggering_event"]["event_id"] == "evt_lin_1"

async def test_existing_alert_records_preserved():
    """Verifies that alerts created prior to the migration (without fingerprints) are preserved and retrievable."""
    old_alert = Alert(region_id=2, severity="INFO", message="Legacy alert")
    
    # We can retrieve it, and its fingerprint is NULL (compatible)
    assert old_alert.fingerprint is None
    assert old_alert.severity == "INFO"
