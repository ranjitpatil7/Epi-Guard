from app.db.base import Base
from app.models.users import User
from app.models.domain import (
    DataSource, Region, EnvironmentalData, WaterQualityRecord, 
    DiseaseRecord, CommunityReport, ModelVersion, RiskAssessment, Alert, AuditLog
)
from app.models.copilot import CopilotConversation, CopilotMessage

# This file imports all models so Alembic can discover them.
