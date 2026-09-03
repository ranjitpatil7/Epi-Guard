"""
Real-Time API Router — JalRakshak AI

Endpoints:
  GET  /realtime/health              — Event bus health check
  POST /realtime/test-events         — Publish test event (DEV only)
  GET  /realtime/ws/intelligence     — WebSocket Command Center

WebSocket authentication:
  Uses JWT token from query parameter ?token=...
  The system currently uses a mocked auth dependency (default user_id=1)
  consistent with the rest of the API. When real JWT auth is deployed,
  replace `_resolve_user_from_token` to call the real `get_current_user` logic.

Security:
  - WebSocket is strictly READ-ONLY from the client perspective.
  - Only "ping" messages are accepted from clients.
  - Any domain mutation attempt terminates the connection.
"""
import json
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.db.redis import redis_manager
from app.realtime.publisher import EventPublisher
from app.realtime.websocket import ws_manager
from app.realtime.ws_events import WebSocketMessage, WSEventType

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Auth helper (compatible with current mocked auth) ─────────────────────────

from jose import jwt, JWTError
from app.core.config import settings

async def _resolve_user_from_token(token: Optional[str]) -> Optional[str]:
    """
    Resolve a user identity from a token using real JWT validation.
    """
    if not token:
        return None
        
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            return None
            
        # Optional: We could query the DB to get the actual user ID from the username,
        # but for realtime WebSocket tracking, storing the username as the client identity is sufficient 
        # (and saves a DB hit on every WS connect).
        # We'll return the username to represent the authenticated identity.
        return username
    except JWTError:
        return None


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/health", summary="Real-time Event Bus Health Check")
async def realtime_health_check() -> Dict[str, Any]:
    """Check Redis and event bus health, including active WebSocket connections."""
    redis_healthy = await redis_manager.ping(retries=1)
    return {
        "status": "healthy" if redis_healthy else "degraded",
        "redis": "healthy" if redis_healthy else "unavailable",
        "event_bus": "active",
        "consumer": "active",
        **ws_manager.get_stats(),
    }


@router.post("/test-events", summary="Publish test event (DEV ONLY)")
async def publish_test_event(
    event_type: str,
    region_id: int,
    payload: Dict[str, Any],
):
    """
    Publish a raw event to the real-time fabric.
    Development / demonstration usage only.
    """
    success = await EventPublisher.publish_event(
        event_type=event_type,
        region_id=region_id,
        source="system_test",
        payload=payload,
    )

    if not success:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail="Failed to publish event to Redis Streams",
        )

    return {"status": "success", "message": f"Event {event_type} published for region {region_id}"}


@router.websocket("/ws/intelligence")
async def websocket_intelligence(
    websocket: WebSocket,
    token: Optional[str] = Query(default=None, alias="token"),
):
    """
    WebSocket Command Center — delivers real-time derived intelligence events.

    Authentication: pass JWT (or dev token) as ?token=<value>
    Protocol: server sends JSON-encoded WebSocketMessage objects
              client may only send {"type": "ping"} heartbeat messages

    SECURITY:
      - Unauthenticated connections are rejected immediately (HTTP 401 close).
      - Domain mutation messages from clients terminate the connection.
      - All outgoing messages are validated against the WSEventType allowlist.
    """
    # ── Step 1: Authenticate before accepting ──────────────────────────────
    user_id = await _resolve_user_from_token(token)
    if user_id is None:
        logger.warning(
            f"WebSocket REJECTED (unauthenticated): "
            f"host={websocket.client.host if websocket.client else 'unknown'}"
        )
        await websocket.close(code=4001, reason="Unauthorized")
        return

    # ── Step 2: Register connection ────────────────────────────────────────
    import uuid
    client_id = str(uuid.uuid4())
    accepted = await ws_manager.connect(websocket, client_id, user_id)
    if not accepted:
        return  # Already closed by ws_manager

    try:
        # ── Step 3: Send welcome / system-status ──────────────────────────
        welcome = WebSocketMessage(
            event_type=WSEventType.SYSTEM_STATUS,
            payload={"status": "connected", "client_id": client_id},
        )
        await websocket.send_text(welcome.model_dump_json())

        # ── Step 4: Receive loop ───────────────────────────────────────────
        while True:
            try:
                raw = await websocket.receive_text()
            except WebSocketDisconnect:
                break

            should_continue = await ws_manager.handle_client_message(client_id, raw)
            if not should_continue:
                logger.warning(
                    f"Client {client_id} sent disallowed message. Closing connection."
                )
                await websocket.close(code=4003, reason="Mutation not allowed")
                break

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.error(f"Unexpected WebSocket error for client {client_id}: {exc}", exc_info=True)
    finally:
        await ws_manager.disconnect(client_id)
