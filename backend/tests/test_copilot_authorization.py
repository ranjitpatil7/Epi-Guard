import pytest
from unittest.mock import patch, MagicMock
from app.copilot.tools import ToolRegistry
from app.copilot.service import process_copilot_message
from app.copilot.schemas import CopilotRequest
from app.models.users import User, UserRole, UserStatus
from app.core.permissions import Permission

@pytest.fixture
def mock_user_admin():
    return User(id=1, username="admin", role=UserRole.ADMINISTRATOR, status=UserStatus.ACTIVE, region_id=None)

@pytest.fixture
def mock_user_gov():
    return User(id=2, username="gov", role=UserRole.GOVERNMENT_OFFICIAL, status=UserStatus.ACTIVE, region_id=None)

@pytest.fixture
def mock_user_epi():
    return User(id=3, username="epi", role=UserRole.EPIDEMIOLOGIST, status=UserStatus.ACTIVE, region_id=None)

@pytest.fixture
def mock_user_field():
    return User(id=4, username="field", role=UserRole.FIELD_OFFICER, status=UserStatus.ACTIVE, region_id=1) # Restricted to region 1

@pytest.fixture
def mock_user_inactive():
    return User(id=5, username="inactive", role=UserRole.ADMINISTRATOR, status=UserStatus.INACTIVE, region_id=None)


@pytest.mark.asyncio
async def test_administrator_allowed_all(mock_user_admin):
    # Admin should be allowed to run any tool
    registry = ToolRegistry(db=MagicMock(), user=mock_user_admin)
    # mock func to prevent actual execution timeouts/errors
    registry.tools["risk_analyst"]["func"] = AsyncMock(return_value={"data": "success"})
    res = await registry.execute_tool("risk_analyst", {"region_name": "test"})
    assert res.success is True

@pytest.mark.asyncio
async def test_gov_official_allowed_permitted(mock_user_gov):
    registry = ToolRegistry(db=MagicMock(), user=mock_user_gov)
    registry.tools["risk_analyst"]["func"] = AsyncMock(return_value={"data": "success"})
    res = await registry.execute_tool("risk_analyst", {"region_name": "test"})
    assert res.success is True

@pytest.mark.asyncio
async def test_epidemiologist_allowed_sir(mock_user_epi):
    registry = ToolRegistry(db=MagicMock(), user=mock_user_epi)
    registry.tools["scenario_analyst"]["func"] = AsyncMock(return_value={"data": "success"})
    res = await registry.execute_tool("scenario_analyst", {"region_name": "test", "changes": {}})
    assert res.success is True

@pytest.mark.asyncio
async def test_field_officer_allowed_field_tool(mock_user_field):
    registry = ToolRegistry(db=MagicMock(), user=mock_user_field)
    registry.tools["get_active_incidents"]["func"] = AsyncMock(return_value={"data": "success"})
    # Mock region id lookup for region 1
    registry._get_region_id = AsyncMock(return_value=1)
    res = await registry.execute_tool("get_active_incidents", {"region_name": "test"})
    assert res.success is True

@pytest.mark.asyncio
async def test_field_officer_denied_audit(mock_user_field):
    registry = ToolRegistry(db=MagicMock(), user=mock_user_field)
    # risk_analyst requires VIEW_RISK which FIELD_OFFICER does not have
    res = await registry.execute_tool("risk_analyst", {"region_name": "test"})
    assert res.success is False
    assert "denied" in res.error.lower()

@pytest.mark.asyncio
async def test_cross_region_denied(mock_user_field):
    registry = ToolRegistry(db=MagicMock(), user=mock_user_field)
    # field officer is restricted to region 1. Let's try region 2.
    registry._get_region_id = AsyncMock(return_value=2)
    res = await registry.execute_tool("get_active_incidents", {"region_name": "other"})
    assert res.success is False
    assert "denied" in res.error.lower()

@pytest.mark.asyncio
async def test_national_scope_allowed(mock_user_admin):
    registry = ToolRegistry(db=MagicMock(), user=mock_user_admin)
    registry._get_region_id = AsyncMock(return_value=2)
    registry.tools["get_active_incidents"]["func"] = AsyncMock(return_value={"data": "success"})
    res = await registry.execute_tool("get_active_incidents", {"region_name": "other"})
    assert res.success is True

@pytest.mark.asyncio
async def test_unauthenticated_denied():
    registry = ToolRegistry(db=MagicMock(), user=None)
    res = await registry.execute_tool("risk_analyst", {"region_name": "test"})
    assert res.success is False
    assert "denied" in res.error.lower()
    
@pytest.mark.asyncio
async def test_inactive_denied(mock_user_inactive):
    registry = ToolRegistry(db=MagicMock(), user=mock_user_inactive)
    res = await registry.execute_tool("risk_analyst", {"region_name": "test"})
    assert res.success is False
    assert "denied" in res.error.lower()

@pytest.mark.asyncio
async def test_unmapped_tool_denied(mock_user_admin):
    registry = ToolRegistry(db=MagicMock(), user=mock_user_admin)
    # inject an unmapped tool
    registry.tools["secret_tool"] = {"func": AsyncMock()}
    res = await registry.execute_tool("secret_tool", {})
    assert res.success is False
    assert "denied" in res.error.lower()

from app.copilot.safety import check_query_safety, SafetyViolation

@pytest.mark.asyncio
async def test_medical_diagnostic_safety():
    with pytest.raises(SafetyViolation) as exc:
        check_query_safety("What medicine should I prescribe for this patient with fever?")
    assert "medical advice" in str(exc.value).lower()

class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)
