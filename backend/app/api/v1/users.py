from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.models.users import User, UserPreference
from app.core.auth_deps import get_current_user

router = APIRouter()

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    region_id: Optional[int] = None

class UserPreferenceUpdate(BaseModel):
    dark_mode: Optional[bool] = None
    animations_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    risk_threshold: Optional[int] = None
    strict_guardrails: Optional[bool] = None
    primary_model: Optional[str] = None
    anomaly_sensitivity: Optional[float] = None
    gemini_api_key: Optional[str] = None
    imd_weather_sync: Optional[bool] = None
    hospital_sync: Optional[bool] = None

@router.patch("/me")
async def update_me(
    profile_update: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Updates the authenticated user's profile."""
    if profile_update.full_name is not None:
        current_user.full_name = profile_update.full_name
    if profile_update.email is not None:
        current_user.email = profile_update.email
    if profile_update.region_id is not None:
        current_user.region_id = profile_update.region_id
        
    await db.commit()
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "region_id": current_user.region_id
    }

@router.get("/me/preferences")
async def get_my_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Gets the authenticated user's preferences, creating defaults if they don't exist."""
    result = await db.execute(select(UserPreference).where(UserPreference.user_id == current_user.id))
    prefs = result.scalars().first()
    
    if not prefs:
        prefs = UserPreference(user_id=current_user.id)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)
        
    return {
        "dark_mode": prefs.dark_mode,
        "animations_enabled": prefs.animations_enabled,
        "email_notifications": prefs.email_notifications,
        "sms_notifications": prefs.sms_notifications,
        "risk_threshold": prefs.risk_threshold,
        "strict_guardrails": prefs.strict_guardrails,
        "primary_model": prefs.primary_model,
        "anomaly_sensitivity": prefs.anomaly_sensitivity,
        "gemini_api_key": prefs.gemini_api_key,
        "imd_weather_sync": prefs.imd_weather_sync,
        "hospital_sync": prefs.hospital_sync
    }

@router.patch("/me/preferences")
async def update_my_preferences(
    pref_update: UserPreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Updates the authenticated user's preferences."""
    result = await db.execute(select(UserPreference).where(UserPreference.user_id == current_user.id))
    prefs = result.scalars().first()
    
    if not prefs:
        prefs = UserPreference(user_id=current_user.id)
        db.add(prefs)
        
    update_data = pref_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prefs, key, value)
        
    await db.commit()
    await db.refresh(prefs)
    
    return {
        "dark_mode": prefs.dark_mode,
        "animations_enabled": prefs.animations_enabled,
        "email_notifications": prefs.email_notifications,
        "sms_notifications": prefs.sms_notifications,
        "risk_threshold": prefs.risk_threshold,
        "strict_guardrails": prefs.strict_guardrails,
        "primary_model": prefs.primary_model,
        "anomaly_sensitivity": prefs.anomaly_sensitivity,
        "gemini_api_key": prefs.gemini_api_key,
        "imd_weather_sync": prefs.imd_weather_sync,
        "hospital_sync": prefs.hospital_sync
    }
from app.core.auth_deps import require_permission
from app.core.permissions import Permission
from app.models.users import UserRole, UserStatus
from app.api.v1.auth import log_audit, get_password_hash, verify_password

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3)
    email: str = Field(..., pattern="^\S+@\S+\.\S+$")
    password: str = Field(..., min_length=8)
    full_name: str
    role: UserRole
    region_id: Optional[int] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

@router.get("")
async def get_users(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permission(Permission.MANAGE_USERS))
):
    result = await db.execute(select(User))
    users = result.scalars().all()
    # Mask password hashes
    return [{"id": u.id, "username": u.username, "email": u.email, "full_name": u.full_name, "role": u.role.value, "status": u.status.value, "region_id": u.region_id} for u in users]

@router.post("")
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permission(Permission.MANAGE_USERS))
):
    admin_id = admin.id
    admin_region_id = admin.region_id
    
    # Enforce region scoping
    if admin_region_id is not None:
        if payload.region_id != admin_region_id:
            raise HTTPException(status_code=403, detail="Region-restricted administrators can only create users for their own region.")
            
    # Check duplicate email
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # Check duplicate username
    result = await db.execute(select(User).where(User.username == payload.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already registered")
        
    hashed_pwd = get_password_hash(payload.password)
    
    new_user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hashed_pwd,
        full_name=payload.full_name,
        role=payload.role,
        region_id=payload.region_id,
        status=UserStatus.ACTIVE
    )
    
    db.add(new_user)
    await db.flush()
    new_user_id = new_user.id
    new_user_username = new_user.username
    new_user_role = new_user.role
    new_user_status = new_user.status
    await db.commit()
    
    await log_audit(db, "USER_CREATED", f"Created user {new_user_username}", admin_id)
    
    return {"id": new_user_id, "username": new_user_username, "role": new_user_role, "status": new_user_status}

@router.patch("/{user_id}/status")
async def update_user_status(
    user_id: int,
    status: UserStatus,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permission(Permission.MANAGE_USERS))
):
    admin_id = admin.id
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    old_status = user.status
    user.status = status
    await db.commit()
    await log_audit(db, "USER_UPDATED", f"Changed status from {old_status} to {status}", admin_id)
    return {"msg": "Status updated"}

@router.patch("/me/password")
async def change_password(
    payload: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
        
    current_user.hashed_password = get_password_hash(payload.new_password)
    await db.commit()
    
    await log_audit(db, "PASSWORD_CHANGED", "User changed their password", user_id)
    return {"msg": "Password updated successfully"}
