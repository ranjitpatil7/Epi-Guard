from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum

class UserRole(str, enum.Enum):
    GOVERNMENT_OFFICIAL = 'GOVERNMENT_OFFICIAL'
    EPIDEMIOLOGIST = 'EPIDEMIOLOGIST'
    FIELD_OFFICER = 'FIELD_OFFICER'
    ADMINISTRATOR = 'ADMINISTRATOR'

class UserStatus(str, enum.Enum):
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
    LOCKED = 'LOCKED'
    PENDING = 'PENDING'

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    
    role = Column(Enum(UserRole), nullable=False)
    region_id = Column(Integer, ForeignKey('regions.id'), nullable=True)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    
    last_login = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relationships
    # Make sure Region is imported or rely on string resolution if base handles it
    sessions = relationship('UserSession', back_populates='user', cascade='all, delete-orphan')
    preferences = relationship('UserPreference', back_populates='user', uselist=False, cascade='all, delete-orphan')

class UserPreference(Base):
    __tablename__ = 'user_preferences'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    
    # Appearance
    dark_mode = Column(Boolean, default=True)
    animations_enabled = Column(Boolean, default=True)
    
    # Notifications
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=True)
    risk_threshold = Column(Integer, default=70)
    
    # AI Config
    strict_guardrails = Column(Boolean, default=True)
    primary_model = Column(String, default="Ensemble (RandomForest + XGBoost)")
    anomaly_sensitivity = Column(Float, default=2.5)
    # Integrations
    gemini_api_key = Column(String, nullable=True)
    imd_weather_sync = Column(Boolean, default=True)
    hospital_sync = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    user = relationship('User', back_populates='preferences')

class UserSession(Base):
    __tablename__ = 'user_sessions'
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    refresh_token_hash = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False)
    device = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    user = relationship('User', back_populates='sessions')
