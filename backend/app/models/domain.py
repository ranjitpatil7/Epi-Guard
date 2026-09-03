from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from geoalchemy2 import Geometry
import enum

class DataTypeEnum(str, enum.Enum):
    REAL = "REAL"
    DEMO = "DEMO"
    SIMULATED = "SIMULATED"

class DataSource(Base):
    __tablename__ = "data_sources"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    source_type = Column(String, nullable=False) # e.g., 'API', 'File'
    url_reference = Column(String)
    collection_timestamp = Column(DateTime(timezone=True))
    ingestion_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    geographic_coverage = Column(String)
    data_quality_score = Column(Float)
    data_type = Column(Enum(DataTypeEnum), default=DataTypeEnum.REAL, nullable=False)
    processing_status = Column(String, default="PENDING")

class Region(Base):
    __tablename__ = "regions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    state = Column(String)
    district = Column(String)
    village = Column(String)
    population = Column(Integer)
    geometry = Column(Geometry('POLYGON', srid=4326))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class EnvironmentalData(Base):
    __tablename__ = "environmental_data"
    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.id"))
    data_source_id = Column(Integer, ForeignKey("data_sources.id"))
    timestamp = Column(DateTime(timezone=True), nullable=False)
    temperature = Column(Float)
    rainfall = Column(Float)
    humidity = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class WaterQualityRecord(Base):
    __tablename__ = "water_quality_records"
    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.id"))
    data_source_id = Column(Integer, ForeignKey("data_sources.id"))
    location = Column(Geometry('POINT', srid=4326))
    turbidity = Column(Float)
    ph = Column(Float)
    coliform_presence = Column(Boolean)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DiseaseRecord(Base):
    __tablename__ = "disease_records"
    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.id"))
    data_source_id = Column(Integer, ForeignKey("data_sources.id"))
    disease_type = Column(String, nullable=False)
    case_count = Column(Integer, nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CommunityReport(Base):
    __tablename__ = "community_reports"
    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"))
    location = Column(Geometry('POINT', srid=4326))
    text_content = Column(Text, nullable=False)
    nlp_severity = Column(Float)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ModelVersion(Base):
    __tablename__ = "model_versions"
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String, nullable=False)
    training_date = Column(DateTime(timezone=True))
    dataset_version = Column(String)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    roc_auc = Column(Float)
    pr_auc = Column(Float)
    calibration = Column(Float)
    false_negatives = Column(Integer)
    false_positives = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.id"))
    model_id = Column(Integer, ForeignKey("model_versions.id"))
    forecast_date = Column(DateTime(timezone=True), nullable=False)
    risk_score = Column(Float, nullable=False)
    shap_explanations = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RiskSnapshot(Base):
    __tablename__ = "risk_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    snapshot_id = Column(String, index=True, nullable=False, unique=True)
    region_id = Column(Integer, ForeignKey("regions.id"), index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), index=True, nullable=False)
    current_risk = Column(Float, nullable=False)
    previous_risk = Column(Float)
    risk_delta = Column(Float)
    ensemble_prediction = Column(Float)
    lower_bound = Column(Float)
    upper_bound = Column(Float)
    confidence = Column(Float)
    anomaly_score = Column(Float)
    spatial_propagation = Column(Float)
    model_version = Column(String)
    feature_version = Column(String)
    triggering_event_id = Column(String, index=True)
    triggering_event_type = Column(String)
    feature_snapshot = Column(JSON)
    explanation_metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.id"), index=True)
    severity = Column(String, nullable=False)
    message = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # New Milestone 3C fields
    fingerprint = Column(String, unique=True, index=True) # Ensure unique constraint for deduplication
    confidence = Column(Float)
    prediction_interval = Column(JSON)
    spatial_factors = Column(JSON)
    temporal_factors = Column(JSON)
    model_version = Column(String)
    triggering_events = Column(JSON)
    risk_snapshot_id = Column(String, ForeignKey("risk_snapshots.snapshot_id"))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String, nullable=False)
    ip_address = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class Anomaly(Base):
    __tablename__ = 'anomalies'
    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey('regions.id'))
    feature = Column(String, nullable=False)
    observed_value = Column(Float)
    expected_mean = Column(Float)
    z_score = Column(Float)
    severity = Column(String)
    explanation = Column(String)
    timestamp = Column(DateTime(timezone=True))
    status = Column(String, default='ACTIVE')
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MLPredictionHistory(Base):
    __tablename__ = 'ml_prediction_history'
    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey('regions.id'))
    prediction_timestamp = Column(DateTime(timezone=True), nullable=False)
    predicted_risk = Column(Float, nullable=False)
    actual_outcome = Column(Float) # Can be updated later
    model_version = Column(String, nullable=False)
    confidence = Column(Float)
    feature_snapshot = Column(JSON)
    explanation = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ModelDriftEvent(Base):
    __tablename__ = 'model_drift_events'
    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String, nullable=False)
    feature_name = Column(String)
    drift_score = Column(Float) # e.g. PSI
    status = Column(String) # NORMAL, WATCH, DRIFT DETECTED
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class IntelligenceEvent(Base):
    __tablename__ = 'intelligence_events'
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, index=True, nullable=False, unique=True)
    event_type = Column(String, index=True, nullable=False)
    region_id = Column(Integer, ForeignKey('regions.id'), index=True)
    source = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), index=True, nullable=False)
    payload = Column(JSON, nullable=False)
    schema_version = Column(String, default="1.0")
    confidence = Column(Float, default=1.0)
    correlation_id = Column(String, index=True)
    processing_status = Column(String, default="PENDING", index=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))

class IncidentSeverity(str, enum.Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class IncidentStatus(str, enum.Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"

class IntelligenceIncident(Base):
    __tablename__ = 'intelligence_incidents'
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String, index=True, nullable=False, unique=True)
    incident_type = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    
    region_id = Column(Integer, ForeignKey('regions.id'), index=True)
    
    severity = Column(Enum(IncidentSeverity), default=IncidentSeverity.INFO, index=True, nullable=False)
    confidence = Column(Float, default=0.0)
    
    status = Column(Enum(IncidentStatus), default=IncidentStatus.OPEN, index=True, nullable=False)
    
    first_detected_at = Column(DateTime(timezone=True), index=True, nullable=False)
    last_updated_at = Column(DateTime(timezone=True), index=True, nullable=False)
    resolved_at = Column(DateTime(timezone=True))
    
    correlation_id = Column(String, index=True)
    
    event_count = Column(Integer, default=0)
    
    source_event_ids = Column(JSON, default=list)
    triggered_rules = Column(JSON, default=list)
    evidence = Column(JSON, default=dict)
    
    spatial_context = Column(JSON, default=dict)
    temporal_context = Column(JSON, default=dict)
    
    risk_before = Column(Float)
    risk_after = Column(Float)
    risk_delta = Column(Float)
    
    signal_diversity = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
class HealthOfficial(Base):
    __tablename__ = 'health_officials'
    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey('regions.id'), index=True, nullable=False)
    name = Column(String, nullable=False)
    contact_number = Column(String, nullable=False)
    email = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
class InventoryItem(Base):
    __tablename__ = 'inventory_items'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    current_stock = Column(Integer, default=0, nullable=False)
    minimum_threshold = Column(Integer, default=100, nullable=False)
    unit = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SupplyDispatch(Base):
    __tablename__ = 'supply_dispatches'
    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey('regions.id'), index=True, nullable=False)
    item_id = Column(Integer, ForeignKey('inventory_items.id'), index=True, nullable=False)
    quantity_dispatched = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

