"""
WebSocket Connection Manager for JalRakshak AI.

This module is responsible for managing WebSocket client connections,
broadcasting derived intelligence events to connected clients, and
enforcing security/backpressure policies.

Responsibilities:
  - Connection registration and cleanup
  - Safe concurrent broadcasting with per-client isolation
  - Maximum connection limit enforcement
  - Stale/dead connection detection and removal
  - Heartbeat acknowledgement
  - Structured logging and observability

This manager is NEVER a source of business logic.
It only delivers already-computed deterministic results from
the backend domain layer (CEP, Risk, Alerts).
"""
import asyncio
import json
import logging
from typing import Dict, Optional, Set
from datetime import datetime, timezone

from fastapi import WebSocket, WebSocketDisconnect

from app.realtime.ws_events import WebSocketMessage, ClientMessage, WSEventType

logger = logging.getLogger(__name__)

# ─── Configuration ─────────────────────────────────────────────────────────────
MAX_CONNECTIONS = 50  # Hard limit on concurrent WebSocket clients
HEARTBEAT_INTERVAL_S = 30  # Seconds between server → client pings
STALE_CONNECTION_TIMEOUT_S = 90  # Mark connection stale if no pong within this time


class _ConnectionRecord:
    """Tracks state for a single connected WebSocket client."""

    def __init__(self, websocket: WebSocket, client_id: str, user_id: Optional[str]):
        self.websocket = websocket
        self.client_id = client_id
        self.user_id = user_id
        self.connected_at: datetime = datetime.now(timezone.utc)
        self.last_seen: datetime = datetime.now(timezone.utc)
        self.messages_sent: int = 0
        self.is_alive: bool = True

    def touch(self):
        self.last_seen = datetime.now(timezone.utc)

    def is_stale(self) -> bool:
        delta = (datetime.now(timezone.utc) - self.last_seen).total_seconds()
        return delta > STALE_CONNECTION_TIMEOUT_S


class WebSocketManager:
    """
    Manages all active WebSocket connections and broadcasting.

    One instance is shared across the FastAPI application (module-level singleton).
    """

    def __init__(self):
        # client_id → _ConnectionRecord
        self._connections: Dict[str, _ConnectionRecord] = {}
        self._lock = asyncio.Lock()
        self._active_connections_gauge: int = 0
        self._total_broadcast_count: int = 0
        self._total_drop_count: int = 0

    # ─── Connection Lifecycle ────────────────────────────────────────────────

    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Accept and register a new WebSocket connection.

        Returns True if the connection was accepted, False if rejected
        (e.g., connection limit reached).
        """
        async with self._lock:
            if len(self._connections) >= MAX_CONNECTIONS:
                logger.warning(
                    f"Connection limit ({MAX_CONNECTIONS}) reached. "
                    f"Rejecting client {client_id}."
                )
                await websocket.close(code=1013, reason="Server connection limit reached")
                return False

            await websocket.accept()
            record = _ConnectionRecord(websocket, client_id, user_id)
            self._connections[client_id] = record
            self._active_connections_gauge = len(self._connections)

        logger.info(
            f"WebSocket CONNECTED: client={client_id} user={user_id} "
            f"total_active={self._active_connections_gauge}"
        )
        return True

    async def disconnect(self, client_id: str):
        """Remove a client from the connection registry."""
        async with self._lock:
            record = self._connections.pop(client_id, None)
            self._active_connections_gauge = len(self._connections)

        if record:
            logger.info(
                f"WebSocket DISCONNECTED: client={client_id} user={record.user_id} "
                f"messages_sent={record.messages_sent} "
                f"total_active={self._active_connections_gauge}"
            )

    # ─── Broadcasting ────────────────────────────────────────────────────────

    async def broadcast(self, message: WebSocketMessage):
        """
        Broadcast a WebSocket message to all connected clients.

        Each client failure is isolated — one broken connection
        will not prevent delivery to others.
        """
        if not message.validate_event_type():
            logger.error(
                f"Refusing to broadcast unknown event type: {message.event_type}"
            )
            self._total_drop_count += 1
            return

        payload_str = message.model_dump_json()

        # Snapshot the list of client IDs to avoid holding the lock during I/O
        async with self._lock:
            client_ids = list(self._connections.keys())

        stale_clients: Set[str] = set()
        success_count = 0

        for client_id in client_ids:
            async with self._lock:
                record = self._connections.get(client_id)

            if record is None:
                continue

            # Enforce cross-user isolation if message specifies a user_id
            if message.user_id is not None and str(record.user_id) != str(message.user_id):
                continue

            if record.is_stale():
                logger.warning(f"Stale client detected: {client_id}. Scheduling cleanup.")
                stale_clients.add(client_id)
                continue

            try:
                await asyncio.wait_for(
                    record.websocket.send_text(payload_str),
                    timeout=5.0,
                )
                record.messages_sent += 1
                success_count += 1
            except asyncio.TimeoutError:
                logger.warning(f"Send timeout for client {client_id}. Scheduling cleanup.")
                stale_clients.add(client_id)
            except Exception as exc:
                logger.warning(f"Failed to send to client {client_id}: {exc}")
                stale_clients.add(client_id)

        # Clean up stale connections
        for client_id in stale_clients:
            await self.disconnect(client_id)

        if client_ids:
            self._total_broadcast_count += 1
            logger.debug(
                f"Broadcast {message.event_type}: delivered={success_count} "
                f"dropped={len(stale_clients)}"
            )

    async def broadcast_system_status(self, status: str, details: Optional[str] = None):
        """Convenience method for SYSTEM_STATUS events."""
        msg = WebSocketMessage(
            event_type=WSEventType.SYSTEM_STATUS,
            payload={"status": status, "details": details or ""},
        )
        await self.broadcast(msg)

    # ─── Heartbeat ───────────────────────────────────────────────────────────

    async def handle_client_message(self, client_id: str, raw_text: str) -> bool:
        """
        Handle a raw text frame from a client.

        ONLY ping/heartbeat messages are accepted.
        Any domain mutation attempt terminates the connection.

        Returns False if the connection should be terminated.
        """
        try:
            data = json.loads(raw_text)
            msg = ClientMessage(**data)
        except Exception:
            logger.warning(
                f"Malformed message from client {client_id}. Terminating connection."
            )
            return False  # Signal to close

        if not msg.is_valid_client_message():
            logger.warning(
                f"Client {client_id} sent disallowed message type '{msg.type}'. "
                f"Terminating connection."
            )
            return False

        # Valid ping — update last_seen and respond with heartbeat_ack
        async with self._lock:
            record = self._connections.get(client_id)
            if record:
                record.touch()

        try:
            ack = WebSocketMessage(event_type=WSEventType.HEARTBEAT_ACK)
            async with self._lock:
                record = self._connections.get(client_id)
            if record:
                await record.websocket.send_text(ack.model_dump_json())
        except Exception:
            pass  # Don't crash if the ack fails — the connection will be pruned eventually

        return True

    # ─── Stats & Shutdown ────────────────────────────────────────────────────

    @property
    def active_connections(self) -> int:
        return self._active_connections_gauge

    def get_stats(self) -> Dict:
        return {
            "active_connections": self._active_connections_gauge,
            "total_broadcasts": self._total_broadcast_count,
            "total_drops": self._total_drop_count,
        }

    async def close_all(self):
        """Gracefully close all active connections during shutdown."""
        async with self._lock:
            client_ids = list(self._connections.keys())

        logger.info(f"Closing {len(client_ids)} active WebSocket connections...")
        for client_id in client_ids:
            async with self._lock:
                record = self._connections.get(client_id)
            if record:
                try:
                    await record.websocket.close(code=1001, reason="Server shutting down")
                except Exception:
                    pass
            await self.disconnect(client_id)


# ─── Singleton ────────────────────────────────────────────────────────────────
ws_manager = WebSocketManager()
