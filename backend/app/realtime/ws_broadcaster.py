"""
WebSocket broadcast helpers for domain services.

Usage:
    from app.realtime.ws_broadcaster import broadcast_ws_event

    # After a successful DB commit:
    await broadcast_ws_event(
        event_type=WSEventType.RISK_RECALCULATED,
        region_id=region_id,
        payload={...},
        severity="HIGH",
    )

IMPORTANT:
  - NEVER call this before the DB transaction commits.
  - The WebSocket is a delivery layer only — no business logic here.
  - Failures are logged but never re-raised (non-critical path).
"""
import json
import logging
from typing import Any, Dict, Optional

from app.db.redis import redis_manager
from app.realtime.ws_events import WebSocketMessage, WSEventType
from app.realtime.pubsub import PUBSUB_CHANNEL

logger = logging.getLogger(__name__)


async def broadcast_ws_event(
    event_type: str,
    payload: Dict[str, Any],
    region_id: Optional[int] = None,
    severity: Optional[str] = None,
    correlation_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> bool:
    """
    Publish a derived intelligence event to the Redis Pub/Sub broadcast channel.

    This function is designed to be called AFTER a successful database commit.
    It will never raise — failures are silently logged so the domain layer is not
    affected by WebSocket delivery issues.

    Returns True on successful publish, False on error.
    """
    try:
        message = WebSocketMessage(
            event_type=event_type,
            region_id=region_id,
            severity=severity,
            correlation_id=correlation_id,
            user_id=user_id,
            payload=payload,
        )

        if not message.validate_event_type():
            logger.error(f"broadcast_ws_event: unknown event type '{event_type}'. Skipped.")
            return False

        redis = redis_manager.get_client()
        await redis.publish(PUBSUB_CHANNEL, message.model_dump_json())
        logger.debug(
            f"WS broadcast published: {event_type} region={region_id} severity={severity}"
        )
        return True

    except Exception as exc:
        logger.warning(
            f"WS broadcast failed for '{event_type}' region={region_id}: {exc}"
        )
        return False
