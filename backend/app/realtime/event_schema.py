from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import uuid

class IntelligenceEvent(BaseModel):
    """
    Base generic event envelope used across the Real-Time Data Fabric.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    region_id: int
    source: str
    payload: Dict[str, Any]
    schema_version: str = "1.0"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    correlation_id: Optional[str] = None

# Specific payload schemas for strong typing if needed by consumers

class RainfallPayload(BaseModel):
    rainfall_mm: float
    duration_hours: float

class RiskChangedPayload(BaseModel):
    old_score: float
    new_score: float
    old_level: str
    new_level: str
    confidence: float

class AnomalyDetectedPayload(BaseModel):
    feature_name: str
    value: float
    expected_range: str
    z_score: float

class ModelDriftPayload(BaseModel):
    metric: str
    value: float
    threshold: float

class InventoryUpdatedPayload(BaseModel):
    item_id: int
    item_name: str
    quantity_deducted: int
    new_stock: int
    minimum_threshold: int
    unit: str
    is_low_stock: bool
