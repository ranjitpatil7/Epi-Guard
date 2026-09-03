import pytest
from app.models.users import UserRole

@pytest.mark.asyncio
async def test_copilot_chat_no_token_returns_401(async_client):
    """Verify that Copilot chat without a token returns 401."""
    response = await async_client.post("/api/v1/copilot/chat", json={"message": "test"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_copilot_investigate_no_token_returns_401(async_client):
    """Verify that Copilot investigate without a token returns 401."""
    response = await async_client.post("/api/v1/copilot/investigate", json={"message": "test"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_copilot_chat_with_valid_token(auth_client_factory):
    """Verify that Copilot chat works with a valid token."""
    client = await auth_client_factory(UserRole.FIELD_OFFICER)
    response = await client.post("/api/v1/copilot/chat", json={"message": "test"})
    assert response.status_code != 401

@pytest.mark.asyncio
async def test_copilot_list_conversations_with_token(auth_client_factory):
    """Verify that listing conversations uses the token to return user's history."""
    client = await auth_client_factory(UserRole.EPIDEMIOLOGIST)
    response = await client.get("/api/v1/copilot/conversations")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
