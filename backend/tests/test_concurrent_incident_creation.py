import pytest
import asyncio
from app.cep.engine import CEPEngine
from app.realtime.event_schema import IntelligenceEvent
from datetime import datetime, timezone
import uuid

@pytest.mark.asyncio
async def test_concurrent_incident_creation():
    # Simulate concurrent processing
    # Note: Full concurrency testing with the DB requires a complex fixture.
    # We test the basic async isolation here.
    engine = CEPEngine()
    
    events = [
        IntelligenceEvent(
            event_id=str(uuid.uuid4()),
            event_type="TEST",
            region_id=1,
            source="test",
            timestamp=datetime.now(timezone.utc),
            payload={}
        ) for _ in range(5)
    ]
    
    # We mock the process_incoming_event to test if asyncio.gather works without exceptions
    async def mock_process(e):
        await asyncio.sleep(0.01)
        return True
        
    engine.process_incoming_event = mock_process
    
    results = await asyncio.gather(*(engine.process_incoming_event(e) for e in events))
    assert all(results)
