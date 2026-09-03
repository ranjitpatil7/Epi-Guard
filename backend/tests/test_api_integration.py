import pytest
from app.models.users import UserRole

@pytest.mark.asyncio
async def test_health_check(async_client):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "JalRakshak AI API is running"}

# --- Authorization Boundary Tests ---

@pytest.mark.asyncio
async def test_no_token_returns_401(async_client):
    """Verify that accessing a protected route without a token returns 401."""
    response = await async_client.get("/api/v1/alerts/")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_insufficient_permission_returns_403(auth_client_factory):
    """Verify that a valid user without MANAGE_USERS permission gets 403 Forbidden."""
    # Field Officer does not have MANAGE_USERS
    client = await auth_client_factory(UserRole.FIELD_OFFICER)
    response = await client.get("/api/v1/users")
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_sufficient_permission_returns_200(auth_client_factory):
    """Verify that a valid user with MANAGE_USERS permission gets 200 OK."""
    # Administrator has MANAGE_USERS
    client = await auth_client_factory(UserRole.ADMINISTRATOR)
    response = await client.get("/api/v1/users")
    assert response.status_code == 200

# --- Protected Endpoint Recovery Tests ---

@pytest.mark.asyncio
async def test_get_alerts(auth_client_factory):
    # Any valid user can view alerts
    client = await auth_client_factory(UserRole.GOVERNMENT_OFFICIAL)
    response = await client.get("/api/v1/alerts/")
    assert response.status_code == 200
    assert "data" in response.json()

@pytest.mark.asyncio
async def test_get_anomalies(auth_client_factory):
    client = await auth_client_factory(UserRole.EPIDEMIOLOGIST)
    response = await client.get("/api/v1/anomalies/")
    assert response.status_code == 200
    assert "data" in response.json()

@pytest.mark.asyncio
async def test_get_community_reports(auth_client_factory):
    client = await auth_client_factory(UserRole.FIELD_OFFICER)
    response = await client.get("/api/v1/community-reports/")
    assert response.status_code == 200
    assert "data" in response.json()

@pytest.mark.asyncio
async def test_get_data_quality(auth_client_factory):
    client = await auth_client_factory(UserRole.ADMINISTRATOR)
    response = await client.get("/api/v1/data-quality/")
    assert response.status_code == 200
    data = response.json()
    assert "overall_quality" in data
    assert "completeness" in data
    assert "freshness" in data
    assert "sources" in data

