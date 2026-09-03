import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from app.realtime.event_schema import IntelligenceEvent
from app.realtime.publisher import EventPublisher
from app.realtime.event_bus import EventBus
from app.realtime.subscriber import EventSubscriber

@pytest.mark.asyncio
async def test_event_schema_validation():
    """Test that event schemas validate correctly."""
    # Valid event
    event = IntelligenceEvent(
        event_type="TEST_EVENT",
        region_id=1,
        source="test_source",
        payload={"key": "value"}
    )
    assert event.event_id is not None
    assert event.confidence == 1.0
    
    # Invalid confidence
    with pytest.raises(ValueError):
        IntelligenceEvent(
            event_type="TEST_EVENT",
            region_id=1,
            source="test_source",
            payload={"key": "value"},
            confidence=1.5 # Should be <= 1.0
        )

@pytest.mark.asyncio
async def test_publisher_mocked():
    """Test the Publisher abstraction with mocked Redis."""
    with patch("app.realtime.event_bus.EventBus.publish", new_callable=AsyncMock) as mock_publish:
        mock_publish.return_value = True
        
        success = await EventPublisher.publish_event(
            event_type="RAINFALL_UPDATE",
            region_id=42,
            source="sensor_net",
            payload={"rainfall_mm": 15.5}
        )
        
        assert success is True
        mock_publish.assert_called_once()
        published_event = mock_publish.call_args[0][0]
        assert published_event.event_type == "RAINFALL_UPDATE"
        assert published_event.region_id == 42

@pytest.mark.asyncio
async def test_subscriber_idempotency():
    """Test subscriber DB idempotency behavior."""
    with patch("app.realtime.subscriber.AsyncSessionLocal") as mock_session_maker:
        mock_session = AsyncMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_session
        
        mock_result = MagicMock()
        mock_existing_event = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_existing_event
        mock_session.execute.return_value = mock_result
        
        event = IntelligenceEvent(
            event_type="TEST_EVENT",
            region_id=1,
            source="test_source",
            payload={"key": "value"}
        )
        
        # When persist is called with "PROCESSED" status
        result = await EventSubscriber._persist_event(event, status="PROCESSED")
        
        assert result is True
        # It should have updated the existing event's status rather than inserting a new one
        assert mock_existing_event.processing_status == "PROCESSED"
        mock_session.add.assert_not_called()
        mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_subscriber_dead_letter():
    """Test dead letter handling."""
    with patch("app.realtime.subscriber.EventSubscriber._persist_event", new_callable=AsyncMock) as mock_persist:
        event = IntelligenceEvent(
            event_type="TEST_EVENT",
            region_id=1,
            source="test",
            payload={}
        )
        
        await EventSubscriber._handle_dead_letter(event, "Test Error")
        
        mock_persist.assert_called_once_with(event, status="DEAD_LETTER", retry_count=EventSubscriber.MAX_RETRIES)

@pytest.mark.asyncio
async def test_subscriber_process_event_success():
    """Test processing a valid event."""
    with patch("app.realtime.subscriber.EventSubscriber._persist_event", new_callable=AsyncMock) as mock_persist:
        mock_persist.return_value = True
        
        event = IntelligenceEvent(
            event_type="TEST_EVENT",
            region_id=1,
            source="test",
            payload={}
        )
        
        success = await EventSubscriber.process_event(event, "1234-0")
        assert success is True
        assert mock_persist.call_count == 2 # Once for PROCESSING, once for PROCESSED

@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_redis_pub_sub():
    """
    Integration test using the real Redis instance.
    This verifies that the real-time fabric components actually work end-to-end.
    """
    from app.db.redis import redis_manager
    await redis_manager.connect()
    redis = redis_manager.get_client()
    
    # We use a unique test stream to avoid polluting the main one
    TEST_STREAM = "jalrakshak:events:integration_test"
    TEST_GROUP = "test_group"
    
    # Ensure stream and group exist
    try:
        await redis.xgroup_create(TEST_STREAM, TEST_GROUP, id="0", mkstream=True)
    except Exception as e:
        if "BUSYGROUP" not in str(e):
            raise
            
    # Publish real event
    event = IntelligenceEvent(
        event_type="INTEGRATION_TEST_EVENT",
        region_id=999,
        source="pytest",
        payload={"test": "data"}
    )
    
    payload_json = event.model_dump_json()
    msg_id = await redis.xadd(TEST_STREAM, {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "data": payload_json
    })
    
    # Consume it
    messages = await redis.xreadgroup(
        TEST_GROUP, 
        "test-consumer", 
        {TEST_STREAM: ">"}, 
        count=1, 
        block=1000
    )
    
    assert messages is not None
    assert len(messages) > 0
    assert len(messages[0][1]) > 0
    
    consumed_msg_id = messages[0][1][0][0]
    consumed_data = messages[0][1][0][1]
    
    assert consumed_msg_id == msg_id
    assert consumed_data["event_type"] == "INTEGRATION_TEST_EVENT"
    
    # Clean up
    await redis.xack(TEST_STREAM, TEST_GROUP, msg_id)
    await redis.delete(TEST_STREAM)
    await redis_manager.disconnect()
