import logging
import json
import asyncio
from typing import List, Callable, Awaitable, Dict, Any, Optional
from redis.asyncio.client import Redis
from redis.exceptions import ResponseError, ConnectionError, TimeoutError
from app.db.redis import redis_manager
from app.realtime.event_schema import IntelligenceEvent

logger = logging.getLogger(__name__)

class EventBus:
    """
    Redis Streams based event bus.
    Provides durable pub/sub with consumer groups.
    """
    
    STREAM_NAME = "jalrakshak:events"
    CONSUMER_GROUP = "cep_processors"
    
    @classmethod
    async def _ensure_group_exists(cls, redis: Redis):
        try:
            # Create stream and group, MKSTREAM creates the stream if it doesn't exist
            await redis.xgroup_create(cls.STREAM_NAME, cls.CONSUMER_GROUP, id="0", mkstream=True)
            logger.info(f"Consumer group {cls.CONSUMER_GROUP} created for stream {cls.STREAM_NAME}.")
        except ResponseError as e:
            if "BUSYGROUP Consumer Group name already exists" not in str(e):
                logger.error(f"Failed to create consumer group: {str(e)}")
                raise

    @classmethod
    async def publish(cls, event: IntelligenceEvent, max_retries: int = 3) -> bool:
        """
        Publishes an event to the Redis stream with bounded retries.
        """
        payload = event.model_dump_json()
        
        # Redis streams require dict of string/bytes
        stream_data = {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "data": payload
        }
        
        for attempt in range(1, max_retries + 1):
            try:
                redis = redis_manager.get_client()
                # Publish event to the stream
                msg_id = await redis.xadd(cls.STREAM_NAME, stream_data)
                logger.info(f"Published event {event.event_id} ({event.event_type}) to {cls.STREAM_NAME} with ID {msg_id}")
                return True
            except (ConnectionError, TimeoutError, Exception) as e:
                logger.warning(f"Failed to publish event (attempt {attempt}/{max_retries}): {str(e)}")
                if attempt < max_retries:
                    await asyncio.sleep(0.5 * attempt)
                else:
                    logger.error(f"Event publish failed after {max_retries} retries: {event.event_id}")
                    return False
        return False

    @classmethod
    async def subscribe(
        cls, 
        consumer_name: str, 
        handler: Callable[[IntelligenceEvent, str], Awaitable[bool]], 
        batch_size: int = 10,
        block_ms: int = 2000
    ):
        """
        Subscribes to the event stream using a consumer group.
        Runs infinitely until cancelled.
        Calls `handler(event, message_id)`. If handler returns True, acks the message.
        """
        redis = redis_manager.get_client()
        await cls._ensure_group_exists(redis)
        
        logger.info(f"Consumer {consumer_name} starting to read from {cls.STREAM_NAME}...")
        
        while True:
            try:
                # Read from the stream ('>' means read new messages never delivered to other consumers in the group)
                messages = await redis.xreadgroup(
                    cls.CONSUMER_GROUP, 
                    consumer_name, 
                    {cls.STREAM_NAME: ">"}, 
                    count=batch_size, 
                    block=block_ms
                )
                
                if messages:
                    for stream, msgs in messages:
                        for msg_id, msg_data in msgs:
                            try:
                                # Parse event
                                data_str = msg_data.get("data")
                                if not data_str:
                                    logger.error(f"Malformed stream message {msg_id}: No data field")
                                    await redis.xack(cls.STREAM_NAME, cls.CONSUMER_GROUP, msg_id)
                                    continue
                                    
                                event = IntelligenceEvent.model_validate_json(data_str)
                                
                                # Process event
                                success = await handler(event, msg_id)
                                
                                if success:
                                    # Acknowledge the message
                                    await redis.xack(cls.STREAM_NAME, cls.CONSUMER_GROUP, msg_id)
                                    logger.debug(f"Acknowledged message {msg_id}")
                            except Exception as e:
                                logger.error(f"Error processing message {msg_id}: {str(e)}", exc_info=True)
                                # We do NOT ack the message if it fails unexpectedly, 
                                # it will go into the PEL (Pending Entries List) for recovery.
                                
            except asyncio.CancelledError:
                logger.info(f"Consumer {consumer_name} cancelled.")
                break
            except (ConnectionError, TimeoutError) as e:
                logger.warning(f"Consumer {consumer_name} redis connection issue: {str(e)}")
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Consumer {consumer_name} unexpected error: {str(e)}", exc_info=True)
                await asyncio.sleep(2)

