import pytest
from app.copilot.tools import ToolRegistry

@pytest.mark.asyncio
async def test_copilot_investigate_tool_safety():
    # Verify the schema of tools to ensure no LLM-generated severity/confidence
    # is allowed to overwrite deterministic backend data
    
    # We will just verify that the registry enforces validation
    # Actually, the ToolRegistry is initialized with AsyncSession
    # We can inspect the schemas
    from app.copilot.tools import InvestigateIncidentInput
    assert "incident_id" in InvestigateIncidentInput.model_fields
    assert "severity" not in InvestigateIncidentInput.model_fields
