from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class CopilotRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    region_id: Optional[int] = None
    request_id: Optional[str] = None

class ExplainRiskRequest(BaseModel):
    contributing_factors: List[Dict[str, Any]]

class ExplainRiskResponse(BaseModel):
    explanation: str

class PredictionInterval(BaseModel):
    lower: float = 0.0
    upper: float = 0.0

class CopilotResponse(BaseModel):
    answer: str = Field(description="Executive Summary / The natural language explanation.")
    risk_level: Optional[str] = Field(None, description="The estimated risk level (e.g. HIGH, MODERATE).")
    prediction_interval: Optional[PredictionInterval] = Field(None, description="Prediction bounds.")
    confidence: float = Field(0.0, description="The confidence percentage.")
    risk_trend: Optional[str] = Field(None, description="e.g., INCREASING, STABLE")
    contributing_factors: List[str] = Field(default_factory=list, description="List of top contributing factors.")
    spatial_factors: List[str] = Field(default_factory=list, description="Spatial influence.")
    forecast: Optional[Dict[str, Any]] = Field(None)
    anomalies: List[str] = Field(default_factory=list)
    alerts: List[str] = Field(default_factory=list)
    scenario_results: Optional[Dict[str, Any]] = Field(None)
    retrieved_evidence: List[Dict[str, str]] = Field(default_factory=list, description="List of dicts with source/excerpt.")
    citations: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list, description="List of tools used.")
    agent_trace: List[Dict[str, Any]] = Field(default_factory=list, description="Execution trace of the agent.")
    data_quality: Optional[float] = Field(None, description="Information about data quality.")
    limitations: Optional[str] = Field(None)
    disclaimer: str = Field("SYNTHETIC DEMONSTRATION DATA. NON-DIAGNOSTIC.", description="Mandatory safety disclaimer.")
