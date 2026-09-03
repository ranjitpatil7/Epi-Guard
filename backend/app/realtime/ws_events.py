"""
Typed WebSocket UI event schemas.

These are DERIVED events — the result of backend domain processing.
They are broadcast to connected React clients over WebSocket.
They must NEVER be used as input for business logic.
"""
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import uuid


# ─── Supported UI event types ────────────────────────────────────────────────
class WSEventType:
    RISK_RECALCULATED = "RISK_RECALCULATED"
    ALERT_CREATED = "ALERT_CREATED"
    ALERT_ESCALATED = "ALERT_ESCALATED"
    ALERT_DEESCALATED = "ALERT_DEESCALATED"
    ALERT_RESOLVED = "ALERT_RESOLVED"
    INTELLIGENCE_INCIDENT_CREATED = "INTELLIGENCE_INCIDENT_CREATED"
    INTELLIGENCE_INCIDENT_UPDATED = "INTELLIGENCE_INCIDENT_UPDATED"
    INTELLIGENCE_INCIDENT_ESCALATED = "INTELLIGENCE_INCIDENT_ESCALATED"
    INTELLIGENCE_INCIDENT_RESOLVED = "INTELLIGENCE_INCIDENT_RESOLVED"
    MODEL_DRIFT_DETECTED = "MODEL_DRIFT_DETECTED"
    SYSTEM_STATUS = "SYSTEM_STATUS"
    HEARTBEAT_ACK = "HEARTBEAT_ACK"
    INVENTORY_UPDATED = "INVENTORY_UPDATED"

    # Copilot Streaming Events
    COPILOT_REQUEST_STARTED = "COPILOT_REQUEST_STARTED"
    AGENT_THINKING = "AGENT_THINKING"
    TOOL_SELECTED = "TOOL_SELECTED"
    TOOL_EXECUTION_STARTED = "TOOL_EXECUTION_STARTED"
    TOOL_EXECUTION_COMPLETED = "TOOL_EXECUTION_COMPLETED"
    TOOL_EXECUTION_FAILED = "TOOL_EXECUTION_FAILED"
    EVIDENCE_RETRIEVED = "EVIDENCE_RETRIEVED"
    RAG_RETRIEVAL_STARTED = "RAG_RETRIEVAL_STARTED"
    RAG_RETRIEVAL_COMPLETED = "RAG_RETRIEVAL_COMPLETED"
    AGENT_SYNTHESIS_STARTED = "AGENT_SYNTHESIS_STARTED"
    FINAL_SYNTHESIS = "FINAL_SYNTHESIS"
    COPILOT_REQUEST_COMPLETED = "COPILOT_REQUEST_COMPLETED"
    COPILOT_REQUEST_FAILED = "COPILOT_REQUEST_FAILED"

    ALLOWED = {
        RISK_RECALCULATED, ALERT_CREATED, ALERT_ESCALATED, ALERT_DEESCALATED,
        ALERT_RESOLVED, INTELLIGENCE_INCIDENT_CREATED, INTELLIGENCE_INCIDENT_UPDATED,
        INTELLIGENCE_INCIDENT_ESCALATED, INTELLIGENCE_INCIDENT_RESOLVED,
        MODEL_DRIFT_DETECTED, SYSTEM_STATUS, HEARTBEAT_ACK, INVENTORY_UPDATED,
        COPILOT_REQUEST_STARTED, AGENT_THINKING, TOOL_SELECTED, TOOL_EXECUTION_STARTED,
        TOOL_EXECUTION_COMPLETED, TOOL_EXECUTION_FAILED, EVIDENCE_RETRIEVED,
        RAG_RETRIEVAL_STARTED, RAG_RETRIEVAL_COMPLETED, AGENT_SYNTHESIS_STARTED,
        FINAL_SYNTHESIS, COPILOT_REQUEST_COMPLETED, COPILOT_REQUEST_FAILED,
    }

    # Event types that are never silently dropped on the client
    CRITICAL_TYPES = {
        ALERT_ESCALATED, INTELLIGENCE_INCIDENT_CREATED, INTELLIGENCE_INCIDENT_ESCALATED,
    }


class WebSocketMessage(BaseModel):
    """
    Standard envelope for all outgoing WebSocket messages.
    
    This schema is strictly for UI delivery.
    It MUST NOT be used as input for business logic.
    """
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    region_id: Optional[int] = None
    correlation_id: Optional[str] = None
    severity: Optional[str] = None
    user_id: Optional[str] = None  # Used for strict cross-user isolation
    payload: Dict[str, Any] = Field(default_factory=dict)

    def validate_event_type(self) -> bool:
        return self.event_type in WSEventType.ALLOWED

    def is_critical(self) -> bool:
        return self.event_type in WSEventType.CRITICAL_TYPES


class ClientMessage(BaseModel):
    """
    Permitted messages from client → server.
    Only heartbeat/ping is accepted.
    """
    type: str  # Must be "ping"

    def is_valid_client_message(self) -> bool:
        return self.type == "ping"
