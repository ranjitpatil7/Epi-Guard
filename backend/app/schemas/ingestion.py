from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class IngestEnvironmentalData(BaseModel):
    region_id: int
    timestamp: datetime
    temperature: Optional[float] = Field(None, ge=-10, le=55, description="Temperature in Celsius")
    rainfall: Optional[float] = Field(None, ge=0, le=2000, description="Rainfall in mm")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="Humidity percentage")

class IngestWaterQualityData(BaseModel):
    region_id: int
    timestamp: datetime
    turbidity: Optional[float] = Field(None, ge=0, le=1000, description="Turbidity in NTU")
    ph: Optional[float] = Field(None, ge=0, le=14, description="pH level")
    coliform_presence: Optional[bool] = Field(None, description="Presence of coliform bacteria")

class IngestDiseaseData(BaseModel):
    region_id: int
    date: datetime
    disease_type: str = Field(..., min_length=2)
    case_count: int = Field(..., ge=0)

class IngestCommunityReport(BaseModel):
    region_id: int
    timestamp: datetime
    text_content: str = Field(..., min_length=5)
    nlp_severity: Optional[float] = Field(None, ge=0, le=1)
