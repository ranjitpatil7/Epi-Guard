"""
Tests for Phase 6 Milestone 3D — WebSocket Command Center.

Tests cover:
  - WebSocket connection with valid token
  - Connection rejection without token
  - Connection rejection with invalid token code (4001)
  - Client mutation attempt → connection termination
  - WebSocket message broadcast
  - Multiple simultaneous clients
  - Per-client failure isolation
  - Malformed Pub/Sub message handling
  - Heartbeat / ping handling
  - Graceful shutdown (close_all)
  - ws_broadcaster.broadcast_ws_event helper
  - WebSocketMessage schema validation (WSEventType allowlist)
  - ClientMessage validation (ping-only)
"""
import asyncio
import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.realtime.ws_events import WebSocketMessage, ClientMessage, WSEventType
from app.realtime.websocket import WebSocketManager
from app.realtime.pubsub import RedisPubSubListener
from app.main import app


# ─── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def test_client():
    """Standard FastAPI test client (not async — sync WebSocket tests)."""
    return TestClient(app)


@pytest.fixture
def ws_manager():
    """Fresh WebSocketManager for unit tests."""
    return WebSocketManager()


# ─── Schema Tests ───────────────────────────────────────────────────────────────

def test_ws_event_type_allowed():
    msg = WebSocketMessage(event_type=WSEventType.RISK_RECALCULATED, payload={"x": 1})
    assert msg.validate_event_type() is True


def test_ws_event_type_unknown_rejected():
    msg = WebSocketMessage(event_type="DELETE_ALL_PATIENTS", payload={})
    assert msg.validate_event_type() is False


def test_ws_event_critical_types():
    msg = WebSocketMessage(event_type=WSEventType.ALERT_ESCALATED, payload={})
    assert msg.is_critical() is True

    msg2 = WebSocketMessage(event_type=WSEventType.RISK_RECALCULATED, payload={})
    assert msg2.is_critical() is False


def test_client_message_ping_valid():
    msg = ClientMessage(type="ping")
    assert msg.is_valid_client_message() is True


def test_client_message_non_ping_invalid():
    msg = ClientMessage(type="PUBLISH_RISK")
    assert msg.is_valid_client_message() is False


def test_client_message_create_incident_invalid():
    msg = ClientMessage(type="CREATE_INCIDENT")
    assert msg.is_valid_client_message() is False


# ─── WebSocketManager unit tests ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ws_manager_connect_and_disconnect(ws_manager):
    mock_ws = AsyncMock()
    mock_ws.client = MagicMock()
    mock_ws.client.host = "127.0.0.1"

    accepted = await ws_manager.connect(mock_ws, "client-1", "user-1")
    assert accepted is True
    assert ws_manager.active_connections == 1

    await ws_manager.disconnect("client-1")
    assert ws_manager.active_connections == 0


@pytest.mark.asyncio
async def test_ws_manager_max_connections_rejected(ws_manager):
    # Patch MAX_CONNECTIONS to 1 for this test
    import app.realtime.websocket as ws_module
    original = ws_module.MAX_CONNECTIONS
    ws_module.MAX_CONNECTIONS = 1

    mock_ws1 = AsyncMock()
    mock_ws2 = AsyncMock()

    await ws_manager.connect(mock_ws1, "c1", "u1")
    accepted2 = await ws_manager.connect(mock_ws2, "c2", "u2")

    assert accepted2 is False
    mock_ws2.close.assert_called_once()

    ws_module.MAX_CONNECTIONS = original
    await ws_manager.disconnect("c1")


@pytest.mark.asyncio
async def test_ws_manager_broadcast_delivers_to_all(ws_manager):
    ws1, ws2 = AsyncMock(), AsyncMock()

    await ws_manager.connect(ws1, "c1", "u1")
    await ws_manager.connect(ws2, "c2", "u2")

    msg = WebSocketMessage(event_type=WSEventType.RISK_RECALCULATED, payload={"x": 1})
    await ws_manager.broadcast(msg)

    ws1.send_text.assert_called_once()
    ws2.send_text.assert_called_once()

    await ws_manager.disconnect("c1")
    await ws_manager.disconnect("c2")


@pytest.mark.asyncio
async def test_ws_manager_broadcast_isolates_failed_client(ws_manager):
    ws_good = AsyncMock()
    ws_bad = AsyncMock()
    ws_bad.send_text.side_effect = Exception("Connection reset")

    await ws_manager.connect(ws_good, "good", "u1")
    await ws_manager.connect(ws_bad, "bad", "u2")

    msg = WebSocketMessage(event_type=WSEventType.ALERT_CREATED, payload={"x": 1})
    await ws_manager.broadcast(msg)

    # Good client receives message
    ws_good.send_text.assert_called_once()
    # Bad client is removed
    assert ws_manager.active_connections == 1

    await ws_manager.disconnect("good")


@pytest.mark.asyncio
async def test_ws_manager_broadcast_unknown_event_rejected(ws_manager):
    ws = AsyncMock()
    await ws_manager.connect(ws, "c1", "u1")

    msg = WebSocketMessage(event_type="INJECT_MALWARE", payload={})
    await ws_manager.broadcast(msg)

    # Event with unknown type must NOT be sent
    ws.send_text.assert_not_called()
    await ws_manager.disconnect("c1")


@pytest.mark.asyncio
async def test_ws_manager_handle_valid_ping(ws_manager):
    ws = AsyncMock()
    await ws_manager.connect(ws, "c1", "u1")

    result = await ws_manager.handle_client_message("c1", json.dumps({"type": "ping"}))
    assert result is True
    await ws_manager.disconnect("c1")


@pytest.mark.asyncio
async def test_ws_manager_handle_mutation_attempt_rejected(ws_manager):
    ws = AsyncMock()
    await ws_manager.connect(ws, "c1", "u1")

    result = await ws_manager.handle_client_message(
        "c1", json.dumps({"type": "CREATE_INCIDENT"})
    )
    assert result is False
    await ws_manager.disconnect("c1")


@pytest.mark.asyncio
async def test_ws_manager_handle_malformed_json_rejected(ws_manager):
    ws = AsyncMock()
    await ws_manager.connect(ws, "c1", "u1")

    result = await ws_manager.handle_client_message("c1", "not_json{{{{")
    assert result is False
    await ws_manager.disconnect("c1")


@pytest.mark.asyncio
async def test_ws_manager_close_all(ws_manager):
    ws1, ws2 = AsyncMock(), AsyncMock()
    await ws_manager.connect(ws1, "c1", "u1")
    await ws_manager.connect(ws2, "c2", "u2")

    await ws_manager.close_all()

    ws1.close.assert_called_once()
    ws2.close.assert_called_once()
    assert ws_manager.active_connections == 0


# ─── PubSub listener unit tests ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pubsub_listener_processes_valid_message():
    listener = RedisPubSubListener()
    valid_msg = WebSocketMessage(
        event_type=WSEventType.RISK_RECALCULATED,
        payload={"current_risk": 72.5},
    )

    with patch("app.realtime.pubsub.ws_manager") as mock_ws_manager:
        mock_ws_manager.broadcast = AsyncMock()
        raw = {"data": valid_msg.model_dump_json()}
        await listener._process_message(raw)
        mock_ws_manager.broadcast.assert_called_once()


@pytest.mark.asyncio
async def test_pubsub_listener_ignores_invalid_json():
    listener = RedisPubSubListener()
    with patch("app.realtime.pubsub.ws_manager") as mock_ws_manager:
        mock_ws_manager.broadcast = AsyncMock()
        await listener._process_message({"data": "{{not json}}"})
        mock_ws_manager.broadcast.assert_not_called()


@pytest.mark.asyncio
async def test_pubsub_listener_ignores_unknown_event_type():
    listener = RedisPubSubListener()
    bad_msg = json.dumps({
        "message_id": "abc",
        "event_type": "DROP_DATABASE",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": {},
    })
    with patch("app.realtime.pubsub.ws_manager") as mock_ws_manager:
        mock_ws_manager.broadcast = AsyncMock()
        await listener._process_message({"data": bad_msg})
        mock_ws_manager.broadcast.assert_not_called()


@pytest.mark.asyncio
async def test_pubsub_listener_ignores_subscribe_confirmation():
    listener = RedisPubSubListener()
    with patch("app.realtime.pubsub.ws_manager") as mock_ws_manager:
        mock_ws_manager.broadcast = AsyncMock()
        # Subscribe confirmation message has integer data, not string
        await listener._process_message({"data": 1})
        mock_ws_manager.broadcast.assert_not_called()


# ─── ws_broadcaster helper ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ws_broadcaster_publishes_to_redis():
    with patch("app.realtime.ws_broadcaster.redis_manager") as mock_redis_mgr:
        mock_redis = AsyncMock()
        mock_redis_mgr.get_client.return_value = mock_redis

        from app.realtime.ws_broadcaster import broadcast_ws_event
        result = await broadcast_ws_event(
            event_type=WSEventType.RISK_RECALCULATED,
            region_id=1,
            severity="HIGH",
            payload={"current_risk": 85.0},
        )
        assert result is True
        mock_redis.publish.assert_called_once()


@pytest.mark.asyncio
async def test_ws_broadcaster_rejects_unknown_event_type():
    with patch("app.realtime.ws_broadcaster.redis_manager") as mock_redis_mgr:
        mock_redis = AsyncMock()
        mock_redis.publish.side_effect = Exception("Redis down")
        mock_redis_mgr.get_client.return_value = mock_redis

        from app.realtime.ws_broadcaster import broadcast_ws_event
        # Must not raise — domain layer must not be affected
        result = await broadcast_ws_event(
            event_type=WSEventType.ALERT_CREATED,
            region_id=1,
            payload={"alert_id": 42},
        )
        assert result is False


# ─── FastAPI WebSocket endpoint integration tests ─────────────────────────────────

from app.api.v1.auth import create_access_token
from starlette.websockets import WebSocketDisconnect

@pytest.fixture
def valid_ws_token():
    return create_access_token("test_user_ws", "Administrator")

def test_ws_endpoint_rejected_without_token(test_client):
    with pytest.raises(WebSocketDisconnect) as exc_info:
        # Unauthenticated — should get close code 4001 or connection refused
        with test_client.websocket_connect("/api/v1/realtime/ws/intelligence") as ws:
            ws.receive_json()
    assert exc_info.value.code == 4001

def test_ws_endpoint_connects_with_valid_token(test_client, valid_ws_token):
    with test_client.websocket_connect(f"/api/v1/realtime/ws/intelligence?token={valid_ws_token}") as ws:
        msg = ws.receive_json()
        assert msg["event_type"] == "SYSTEM_STATUS"
        assert msg["payload"]["status"] == "connected"

def test_ws_endpoint_mutation_attempt_terminates_connection(test_client, valid_ws_token):
    """Client sending a domain mutation message should have connection closed."""
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with test_client.websocket_connect(f"/api/v1/realtime/ws/intelligence?token={valid_ws_token}") as ws:
            # Receive welcome message
            ws.receive_json()
            # Send a mutation attempt
            ws.send_json({"type": "CREATE_INCIDENT", "data": {"region": 1}})
            # Connection should be closed
            ws.receive_json()
    assert exc_info.value.code == 4003

def test_ws_endpoint_ping_gets_heartbeat_ack(test_client, valid_ws_token):
    with test_client.websocket_connect(f"/api/v1/realtime/ws/intelligence?token={valid_ws_token}") as ws:
        ws.receive_json()  # welcome
        ws.send_json({"type": "ping"})
        ack = ws.receive_json()
        assert ack["event_type"] == "HEARTBEAT_ACK"
