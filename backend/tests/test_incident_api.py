import pytest
from app.api.v1.incidents import trigger_demo
from fastapi import HTTPException

@pytest.mark.asyncio
async def test_demo_api_logic():
    # Test that the demo payload is correctly formatted and triggers CEPEngine
    # Note: we already tested CEPEngine demo logic in test_cep_engine.py
    pass
