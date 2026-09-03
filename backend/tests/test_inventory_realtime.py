import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.inventory_service import InventoryService
from app.models.domain import InventoryItem, SupplyDispatch

@pytest.fixture
def mock_db_session():
    session = AsyncMock(spec=AsyncSession)
    
    # Setup mock item
    mock_item = MagicMock(spec=InventoryItem)
    mock_item.id = 1
    mock_item.name = "ORS Packets"
    mock_item.current_stock = 1000
    mock_item.minimum_threshold = 200
    mock_item.unit = "packets"
    
    # Mock db.execute(select(...))
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_item
    session.execute.return_value = mock_result
    
    return session, mock_item

@pytest.mark.asyncio
@patch("app.services.inventory_service.EventBus.publish")
@patch("app.services.inventory_service.broadcast_ws_event")
async def test_successful_deduction_emits_events(mock_broadcast, mock_publish, mock_db_session):
    db, mock_item = mock_db_session
    
    response = await InventoryService.deduct_stock(db, region_id=2, deductions=[("ORS Packets", 100)])
    
    # DB updates
    assert mock_item.current_stock == 900
    assert db.add.called
    assert db.commit.called
    
    # Events should be emitted
    assert mock_publish.called
    assert mock_broadcast.called
    
    # Check WS broadcast payload
    call_kwargs = mock_broadcast.call_args.kwargs
    assert call_kwargs["event_type"] == "INVENTORY_UPDATED"
    assert call_kwargs["payload"]["item_name"] == "ORS Packets"
    assert call_kwargs["payload"]["quantity_deducted"] == 100
    assert call_kwargs["payload"]["new_stock"] == 900
    assert call_kwargs["payload"]["is_low_stock"] is False

@pytest.mark.asyncio
@patch("app.services.inventory_service.EventBus.publish")
@patch("app.services.inventory_service.broadcast_ws_event")
async def test_low_stock_deduction_emits_events_with_flag(mock_broadcast, mock_publish, mock_db_session):
    db, mock_item = mock_db_session
    # Item starts at 1000, min is 200. Deducting 900 brings it to 100 (LOW STOCK)
    response = await InventoryService.deduct_stock(db, region_id=2, deductions=[("ORS Packets", 900)])
    
    assert mock_item.current_stock == 100
    
    # Check WS broadcast payload
    call_kwargs = mock_broadcast.call_args.kwargs
    assert call_kwargs["payload"]["new_stock"] == 100
    assert call_kwargs["payload"]["is_low_stock"] is True

@pytest.mark.asyncio
@patch("app.services.inventory_service.EventBus.publish")
@patch("app.services.inventory_service.broadcast_ws_event")
async def test_failed_deduction_no_item_no_events(mock_broadcast, mock_publish, mock_db_session):
    db, mock_item = mock_db_session
    # Make db return None for item
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    db.execute.return_value = mock_result
    
    response = await InventoryService.deduct_stock(db, region_id=2, deductions=[("ORS Packets", 100)])
    
    assert not mock_publish.called
    assert not mock_broadcast.called

@pytest.mark.asyncio
@patch("app.services.inventory_service.EventBus.publish")
@patch("app.services.inventory_service.broadcast_ws_event")
async def test_db_commit_failure_prevents_events(mock_broadcast, mock_publish, mock_db_session):
    db, mock_item = mock_db_session
    db.commit.side_effect = Exception("DB Connection Lost")
    
    with pytest.raises(Exception):
        await InventoryService.deduct_stock(db, region_id=2, deductions=[("ORS Packets", 100)])
        
    # Events MUST NOT be published if DB fails
    assert not mock_publish.called
    assert not mock_broadcast.called

@pytest.mark.asyncio
@patch("app.services.inventory_service.EventBus.publish")
@patch("app.services.inventory_service.broadcast_ws_event")
async def test_publish_failure_does_not_rollback_db(mock_broadcast, mock_publish, mock_db_session):
    db, mock_item = mock_db_session
    mock_publish.side_effect = Exception("Redis Down")
    
    # Should not raise exception
    response = await InventoryService.deduct_stock(db, region_id=2, deductions=[("ORS Packets", 100)])
    
    # DB transaction was already committed successfully
    assert mock_item.current_stock == 900
    assert db.commit.called
    assert response["status"] == "success"
