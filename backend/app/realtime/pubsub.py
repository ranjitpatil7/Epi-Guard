"""
Redis Pub/Sub listener for WebSocket broadcasting.

Architecture:
  Domain Services → redis.publish("jalrakshak:ws:broadcast", json) 
                  → RedisPubSubListener 
                  → WebSocketManager.broadcast()

This module runs as a single background task started during FastAPI lifespan.

Key guarantees:
  - Never crashes the application on Redis disconnection (reconnects automatically)
  - Validates all incoming Pub/Sub messages before forwarding to WebSocket clients
  - Shuts down cleanly during application lifespan termination
  - Does NOT perform any domain/business logic — it is a delivery layer only
"""
import asyncio
import json
import logging

from app.db.redis import redis_manager
from app.realtime.ws_events import WebSocketMessage, WSEventType
from app.realtime.websocket import ws_manager

logger = logging.getLogger(__name__)

# ─── Configuration ─────────────────────────────────────────────────────────────
PUBSUB_CHANNEL = "jalrakshak:ws:broadcast"
RECONNECT_BASE_DELAY_S = 2.0
RECONNECT_MAX_DELAY_S = 30.0


class RedisPubSubListener:
    """
    Subscribes to the Redis Pub/Sub broadcast channel and forwards
    valid messages to the WebSocketManager.

    One instance is created and started during FastAPI application startup.
    """

    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self):
        """Start the background listener task."""
        if self._task and not self._task.done():
            logger.warning("RedisPubSubListener is already running.")
            return
        self._running = True
        self._task = asyncio.create_task(self._run_forever(), name="redis_pubsub_listener")
        logger.info(f"RedisPubSubListener started, channel: {PUBSUB_CHANNEL}")

    async def stop(self):
        """Signal the listener to stop and wait for clean exit."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
        logger.info("RedisPubSubListener stopped.")

    async def _run_forever(self):
        """
        Main loop: connect to Redis Pub/Sub, listen for messages,
        and reconnect automatically on failure.
        """
        delay = RECONNECT_BASE_DELAY_S

        while self._running:
            try:
                await self._listen()
                # If _listen returns normally, the channel was closed
                if self._running:
                    logger.warning("Pub/Sub channel closed. Reconnecting...")
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, RECONNECT_MAX_DELAY_S)
            except asyncio.CancelledError:
                logger.info("RedisPubSubListener cancelled.")
                break
            except Exception as exc:
                if not self._running:
                    break
                logger.error(f"RedisPubSubListener error: {exc}. Reconnecting in {delay}s...")
                await asyncio.sleep(delay)
                delay = min(delay * 2, RECONNECT_MAX_DELAY_S)

    async def _listen(self):
        """
        Subscribe to the Pub/Sub channel and forward messages.
        Exits if self._running becomes False or on connection error.
        """
        redis = redis_manager.get_client()
        pubsub = redis.pubsub()

        try:
            await pubsub.subscribe(PUBSUB_CHANNEL)
            logger.info(f"Subscribed to Redis Pub/Sub channel: {PUBSUB_CHANNEL}")

            while self._running:
                # Non-blocking read with a short timeout so we can check _running
                raw = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )

                if raw is None:
                    continue

                await self._process_message(raw)

        finally:
            try:
                await pubsub.unsubscribe(PUBSUB_CHANNEL)
                await pubsub.aclose()
            except Exception:
                pass

    async def _process_message(self, raw: dict):
        """
        Parse, validate, and forward a single Pub/Sub message.
        Any malformed message is logged and discarded — never propagated.
        """
        data = raw.get("data")
        if not isinstance(data, str):
            return  # Subscribe/unsubscribe confirmation messages

        try:
            parsed = json.loads(data)
        except json.JSONDecodeError:
            logger.warning(f"Pub/Sub: received non-JSON data: {data[:200]}")
            return

        try:
            message = WebSocketMessage(**parsed)
        except Exception as exc:
            logger.warning(f"Pub/Sub: invalid WebSocketMessage schema: {exc}")
            return

        if not message.validate_event_type():
            logger.warning(
                f"Pub/Sub: unknown event_type '{message.event_type}'. Discarding."
            )
            return

        logger.debug(
            f"Pub/Sub → WS: {message.event_type} region={message.region_id} "
            f"severity={message.severity}"
        )
        await ws_manager.broadcast(message)


# ─── Singleton ────────────────────────────────────────────────────────────────
pubsub_listener = RedisPubSubListener()
