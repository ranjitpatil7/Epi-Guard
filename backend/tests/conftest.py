import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.config import settings
from sqlalchemy.pool import NullPool

# Use the real database for read-only integration tests
TEST_DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True)
async def db_setup():
    # Do not create/drop tables to protect dev data
    yield

@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

import uuid
from app.models.users import User, UserRole, UserStatus
from app.core.security import get_password_hash
from app.api.v1.auth import create_access_token

@pytest_asyncio.fixture
async def auth_client_factory(async_client):
    """Factory to get an authenticated client with a specific role."""
    created_users = []
    
    async def _get_client(role: UserRole = UserRole.ADMINISTRATOR):
        # Create temporary user in DB
        username = f"test_{uuid.uuid4().hex[:8]}"
        user = User(
            username=username,
            email=f"{username}@test.com",
            hashed_password=get_password_hash("testpass"),
            full_name="Test User",
            role=role,
            status=UserStatus.ACTIVE
        )
        
        async with TestingSessionLocal() as db:
            db.add(user)
            await db.commit()
            await db.refresh(user)
            created_users.append(user.id)
            
        # Generate valid JWT
        token = create_access_token(user.username, role.value)
        async_client.headers.update({"Authorization": f"Bearer {token}"})
        return async_client
        
    yield _get_client
    
    # Cleanup all created users
    async with TestingSessionLocal() as db:
        for uid in created_users:
            user = await db.get(User, uid)
            if user:
                await db.delete(user)
        await db.commit()
