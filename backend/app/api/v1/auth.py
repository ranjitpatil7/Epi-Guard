import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt
from passlib.context import CryptContext

from app.db.session import get_db
from app.core.config import settings
from app.models.users import User, UserSession, UserStatus, UserRole
from app.models.domain import AuditLog
from app.core.auth_deps import get_current_user, require_permission
from app.core.permissions import Permission, get_permissions_for_role

router = APIRouter()
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(subject: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject), "role": role}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def log_audit(db: AsyncSession, event_type: str, details: str, user_id: int = None, region_id: int = None):
    log = AuditLog(
        user_id=user_id,
        action=f"{event_type}: {details}",
        ip_address="127.0.0.1" # Mock IP for now
    )
    db.add(log)
    await db.commit()

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Any:
    # Authenticate user
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalars().first()
    
    if not user:
        await log_audit(db, "LOGIN_FAILED", f"Invalid username: {form_data.username}")
        raise HTTPException(status_code=400, detail="Incorrect username or password")
        
    if user.status == UserStatus.LOCKED:
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            await log_audit(db, "LOGIN_REJECTED", "Account locked", user.id)
            raise HTTPException(status_code=403, detail="Account is locked. Try again later.")
        else:
            user.status = UserStatus.ACTIVE
            user.failed_login_attempts = 0
            user.locked_until = None
            
    if user.status != UserStatus.ACTIVE:
        await log_audit(db, "LOGIN_REJECTED", f"Account status: {user.status}", user.id)
        raise HTTPException(status_code=403, detail="Account is inactive")
        
    if not verify_password(form_data.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.status = UserStatus.LOCKED
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
            await log_audit(db, "ACCOUNT_LOCKED", "Exceeded max login attempts", user.id)
        await db.commit()
        await log_audit(db, "LOGIN_FAILED", "Invalid password", user.id)
        raise HTTPException(status_code=400, detail="Incorrect username or password")
        
    # Success
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.now(timezone.utc)
    
    # Generate tokens
    access_token = create_access_token(user.username, user.role.value)
    
    # Create refresh token (secure random)
    refresh_token = str(uuid.uuid4())
    refresh_token_hash = pwd_context.hash(refresh_token)
    
    session_id = str(uuid.uuid4())
    user_session = UserSession(
        id=session_id,
        user_id=user.id,
        refresh_token_hash=refresh_token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    db.add(user_session)
    await db.commit()
    
    await log_audit(db, "LOGIN_SUCCESS", "User logged in", user.id, user.region_id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "session_id": session_id,
        "token_type": "bearer",
        "user": {
            "username": user.username,
            "role": user.role,
            "permissions": list(get_permissions_for_role(user.role))
        }
    }

@router.post("/refresh")
async def refresh_token(
    session_id: str,
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(UserSession).where(UserSession.id == session_id))
    user_session = result.scalars().first()
    
    if not user_session or user_session.revoked or user_session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Invalid session")
        
    if not verify_password(refresh_token, user_session.refresh_token_hash):
        raise HTTPException(status_code=401, detail="Invalid token")
        
    result_user = await db.execute(select(User).where(User.id == user_session.user_id))
    user = result_user.scalars().first()
    
    if not user or user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=401, detail="User inactive")
        
    access_token = create_access_token(user.username, user.role.value)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(UserSession).where(UserSession.id == session_id))
    user_session = result.scalars().first()
    if user_session and user_session.user_id == current_user.id:
        user_session.revoked = True
        await db.commit()
    
    await log_audit(db, "LOGOUT", "User logged out", current_user.id)
    return {"msg": "Logged out successfully"}

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    permissions = get_permissions_for_role(current_user.role)
    return {
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "region_id": current_user.region_id,
        "status": current_user.status,
        "permissions": [p.value for p in permissions]
    }

# --- Admin User Management moved to users.py ---
