import logging
from typing import Any, Dict, Optional
from datetime import datetime, timezone

from app.realtime.ws_broadcaster import broadcast_ws_event

logger = logging.getLogger(__name__)

async def broadcast_copilot_event(
    event_type: str,
    conversation_id: int,
    request_id: str,
    sequence_number: int,
    payload: Dict[str, Any],
    user_id: int
) -> None:
    """
    Broadcasts a Copilot execution state event via the WebSocket infrastructure.
    
    This function is strictly for streaming non-sensitive execution states
    to the UI. It MUST NOT include raw LLM responses, system prompts, or 
    chain-of-thought tokens.
    
    Cross-user isolation is enforced by passing the `user_id`, which the
    WebSocketManager uses to filter broadcast targets.
    
    Failures are logged silently. Copilot execution should NEVER be interrupted
    by a streaming delivery failure.
    """
    try:
        enriched_payload = {
            **payload,
            "conversation_id": conversation_id,
            "request_id": request_id,
            "sequence_number": sequence_number,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await broadcast_ws_event(
            event_type=event_type,
            payload=enriched_payload,
            user_id=str(user_id)
        )
    except Exception as e:
        logger.warning(f"Failed to broadcast copilot event {event_type} (req: {request_id}): {e}")
