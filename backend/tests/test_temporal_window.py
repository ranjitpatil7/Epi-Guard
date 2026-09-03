import pytest
from datetime import datetime, timezone, timedelta
import uuid
from app.realtime.event_schema import IntelligenceEvent
from app.cep.window import TemporalWindowEngine

def _make_event(dt):
    return IntelligenceEvent(
        event_id=str(uuid.uuid4()),
        event_type="TEST",
        region_id=1,
        source="test",
        timestamp=dt,
        payload={},
        correlation_id="test"
    )

def test_temporal_window_inclusive():
    base_time = datetime.now(timezone.utc)
    events = [
        _make_event(base_time - timedelta(hours=2)),
        _make_event(base_time - timedelta(hours=1)),
        _make_event(base_time)
    ]
    
    # 1.5 hour window
    filtered = TemporalWindowEngine.get_events_in_window(events, timedelta(hours=1, minutes=30), base_time)
    assert len(filtered) == 2
    assert filtered[0].timestamp == events[1].timestamp
    
def test_temporal_window_out_of_order():
    base_time = datetime.now(timezone.utc)
    events = [
        _make_event(base_time),
        _make_event(base_time - timedelta(hours=2)),
        _make_event(base_time - timedelta(hours=1))
    ]
    
    filtered = TemporalWindowEngine.get_events_in_window(events, timedelta(hours=1, minutes=30), base_time)
    assert len(filtered) == 2
    # Ensure they are sorted
    assert filtered[0].timestamp < filtered[1].timestamp

def test_temporal_window_future_timestamps():
    base_time = datetime.now(timezone.utc)
    events = [
        _make_event(base_time - timedelta(hours=1)),
        _make_event(base_time + timedelta(hours=1)) # Future event
    ]
    
    # We also want to exclude events in the future (beyond reference_time)
    filtered = TemporalWindowEngine.get_events_in_window(events, timedelta(hours=2), base_time)
    # The future event is excluded
    assert len(filtered) == 1

def test_empty_window():
    base_time = datetime.now(timezone.utc)
    filtered = TemporalWindowEngine.get_events_in_window([], timedelta(hours=1), base_time)
    assert len(filtered) == 0

def test_exact_boundary():
    base_time = datetime.now(timezone.utc)
    events = [
        _make_event(base_time - timedelta(hours=1))
    ]
    filtered = TemporalWindowEngine.get_events_in_window(events, timedelta(hours=1), base_time)
    assert len(filtered) == 1
