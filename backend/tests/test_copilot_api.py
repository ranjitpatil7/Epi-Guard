import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.copilot.service import process_copilot_message
from app.copilot.schemas import CopilotRequest, CopilotResponse
from app.copilot.safety import SafetyViolation
import json

@pytest.mark.asyncio
async def test_process_copilot_message_valid():
    mock_db = AsyncMock()
    # Mock conversation lookup
    mock_db.get.return_value = MagicMock(id=1, user_id=1)
    
    # Mock history query
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    request = CopilotRequest(message="Which regions have highest risk?", conversation_id=1)
    
    mock_provider = AsyncMock()
    # We mock the provider returning the final synthesis immediately (iteration 1)
    mock_provider.generate_response.return_value = (
        json.dumps({
            "action": "final_response",
            "executive_summary": "Assam has the highest risk.",
            "risk_level": "HIGH",
            "confidence": 0.85,
            "evidence": ["test evidence"],
            "contributing_factors": [],
            "alerts": [],
            "anomalies": [],
            "recommended_actions": [],
            "sources": ["Risk API"],
            "disclaimer": "SYNTHETIC VALIDATION DATA."
        }),
        []
    )
    
    with patch("app.copilot.service.get_llm_provider", return_value=mock_provider):
        response = await process_copilot_message(mock_db, request, user_id=1)
        assert response.answer == "Assam has the highest risk."
        assert response.risk_level == "HIGH"
        # Since it didn't call any tools in our mock iteration, sources will be empty
        assert response.sources == []
        assert response.agent_trace[0]["action"] == "final_synthesis"

@pytest.mark.asyncio
async def test_process_copilot_message_safety_blocked():
    mock_db = AsyncMock()
    request = CopilotRequest(message="do I have cholera", conversation_id=1)
    
    with pytest.raises(SafetyViolation):
        await process_copilot_message(mock_db, request, user_id=1)
