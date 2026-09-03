from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.models.domain import IncidentSeverity, IncidentStatus

class CEPPatternMatch(BaseModel):
    rule_id: str
    matched: bool
    score: float
    confidence: float
    event_ids: List[str]
    region_ids: List[int]
    evidence: Dict[str, Any]
    spatial_context: Dict[str, Any]
    temporal_context: Dict[str, Any]
    explanation: str

class IntelligenceIncidentCreate(BaseModel):
    incident_type: str
    title: str
    description: str
    region_id: int
    severity: IncidentSeverity
    confidence: float
    correlation_id: Optional[str] = None
    source_event_ids: List[str] = Field(default_factory=list)
    triggered_rules: List[str] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    spatial_context: Dict[str, Any] = Field(default_factory=dict)
    temporal_context: Dict[str, Any] = Field(default_factory=dict)
    risk_before: Optional[float] = None
    risk_after: Optional[float] = None
    risk_delta: Optional[float] = None
    signal_diversity: float = 0.0
    first_detected_at: datetime
    last_updated_at: datetime

class IntelligenceIncidentResponse(IntelligenceIncidentCreate):
    id: int
    incident_id: str
    status: IncidentStatus
    event_count: int
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
