from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from app.db.session import get_db
from app.services.inventory_service import InventoryService

router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def get_inventory(db: AsyncSession = Depends(get_db)):
    """
    Returns current stock levels for all inventory items.
    """
    items = await InventoryService.get_all_inventory(db)
    return {
        "items": [
            {
                "id": item.id,
                "name": item.name,
                "current_stock": item.current_stock,
                "minimum_threshold": item.minimum_threshold,
                "unit": item.unit,
                "is_low_stock": item.current_stock < item.minimum_threshold,
            }
            for item in items
        ]
    }
