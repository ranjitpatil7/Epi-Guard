from datetime import datetime, timezone
from typing import Annotated, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.core.config import settings
from app.models.users import User, UserStatus
from app.core.permissions import Permission, get_permissions_for_role

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    
    if user is None:
        raise credentials_exception
        
    if user.status != UserStatus.ACTIVE:
        # Check if they were locked and time has passed
        if user.status == UserStatus.LOCKED and user.locked_until and user.locked_until < datetime.now(timezone.utc):
            user.status = UserStatus.ACTIVE
            user.failed_login_attempts = 0
            user.locked_until = None
            await db.commit()
        else:
            raise HTTPException(status_code=403, detail="Inactive or locked user")
            
    return user

def require_permission(required_permission: Permission):
    async def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        user_permissions = get_permissions_for_role(current_user.role)
        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Requires {required_permission.value}"
            )
        return current_user
    return permission_checker
