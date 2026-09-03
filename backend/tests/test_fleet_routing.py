import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.logistics_service import calculate_optimal_route, haversine, COMMAND_HUB_COORDS

@pytest.mark.asyncio
async def test_calculate_optimal_route_valid_regions():
    # Mock DB
    mock_db = AsyncMock()
    
    mock_result = MagicMock()
    mock_result.all.return_value = [
        MagicMock(id=1, name="Region 1", lat=28.0, lng=77.0),
        MagicMock(id=99, name="Region 99", lat=19.0, lng=72.0)
    ]
    mock_db.execute.return_value = mock_result
    
    route_data = await calculate_optimal_route(mock_db, [1, 99])
    
    assert len(route_data["route"]) == 4
    assert route_data["route"][0]["id"] == "HUB"
    assert route_data["route"][-1]["id"] == "HUB"
    
    visited_ids = [stop["id"] for stop in route_data["route"]]
    assert 1 in visited_ids
    assert 99 in visited_ids
    assert route_data["total_distance_km"] > 0
    assert route_data["estimated_time_hrs"] > 0

@pytest.mark.asyncio
async def test_calculate_optimal_route_missing_region():
    mock_db = AsyncMock()
    
    # DB only returns region 1, but requested 1 and 2
    mock_result = MagicMock()
    mock_result.all.return_value = [
        MagicMock(id=1, name="Region 1", lat=28.0, lng=77.0)
    ]
    mock_db.execute.return_value = mock_result
    
    with pytest.raises(ValueError) as exc:
        await calculate_optimal_route(mock_db, [1, 2])
        
    assert "Invalid or missing region IDs provided" in str(exc.value)
    assert "2" in str(exc.value)
    
@pytest.mark.asyncio
async def test_calculate_optimal_route_missing_geometry():
    mock_db = AsyncMock()
    
    mock_result = MagicMock()
    mock_result.all.return_value = [
        MagicMock(id=1, name="Region 1", lat=None, lng=77.0)
    ]
    mock_db.execute.return_value = mock_result
    
    with pytest.raises(ValueError) as exc:
        await calculate_optimal_route(mock_db, [1])
        
    assert "no valid geometry coordinates" in str(exc.value)

def test_haversine_distance_correctness():
    # Test distance between Delhi and Mumbai roughly
    dist = haversine(28.6139, 77.2090, 19.0760, 72.8777)
    # Should be around 1148 km
    assert 1100 < dist < 1200
