from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging
from app.realtime.event_schema import IntelligenceEvent
from app.realtime.event_bus import EventBus

logger = logging.getLogger(__name__)

class EventPublisher:
    """
    Business logic abstraction for publishing intelligence events.
    Services should use this class rather than EventBus directly.
    """
    
    @staticmethod
    async def publish_event(
        event_type: str, 
        region_id: int, 
        source: str, 
        payload: Dict[str, Any],
        confidence: float = 1.0,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Creates and publishes an IntelligenceEvent.
        """
        try:
            event = IntelligenceEvent(
                event_type=event_type,
                region_id=region_id,
                source=source,
                payload=payload,
                confidence=confidence,
                correlation_id=correlation_id,
                timestamp=datetime.now(timezone.utc)
            )
            
            success = await EventBus.publish(event)
            if success:
                logger.info(f"Successfully published {event_type} event for region {region_id}")
            else:
                logger.error(f"Failed to publish {event_type} event for region {region_id}")
            return success
        except Exception as e:
            logger.error(f"Error publishing {event_type} event: {str(e)}", exc_info=True)
            return False
