import logging
from typing import List, Dict, Tuple, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.domain import InventoryItem, SupplyDispatch
from app.realtime.event_schema import IntelligenceEvent, InventoryUpdatedPayload
from app.realtime.event_bus import EventBus
from app.realtime.ws_events import WSEventType
from app.realtime.ws_broadcaster import broadcast_ws_event

logger = logging.getLogger(__name__)

class InventoryService:
    """
    Manages physical supply chain inventory (ORS, Water Tablets, Vaccines).
    """

    @staticmethod
    async def get_all_inventory(db: AsyncSession) -> List[InventoryItem]:
        """Fetches current stock levels for all inventory items."""
        result = await db.execute(select(InventoryItem).order_by(InventoryItem.id))
        return result.scalars().all()

    @staticmethod
    async def deduct_stock(db: AsyncSession, region_id: int, deductions: List[Tuple[str, int]]) -> Dict[str, Any]:
        """
        Deducts specific quantities of stock and records the dispatch.
        `deductions` is a list of tuples: (item_name, quantity_to_deduct)
        """
        response = {"status": "success", "warnings": []}
        successful_updates = []

        for item_name, qty in deductions:
            # 1. Fetch item by name
            result = await db.execute(select(InventoryItem).filter(InventoryItem.name == item_name))
            item = result.scalars().first()

            if not item:
                logger.error(f"Inventory item '{item_name}' not found.")
                continue

            # 2. Check stock capacity
            if item.current_stock < qty:
                response["warnings"].append(f"Insufficient stock for {item_name}. Requested {qty}, available {item.current_stock}.")
                qty = item.current_stock # Drain the remaining stock if insufficient

            if qty <= 0:
                continue

            # 3. Deduct stock
            item.current_stock -= qty
            is_low_stock = item.current_stock < item.minimum_threshold

            # 4. Check low stock threshold
            if is_low_stock:
                logger.warning(f"⚠️ LOW STOCK ALERT: {item.name} is below minimum threshold ({item.current_stock} < {item.minimum_threshold})")
                response["warnings"].append(f"LOW STOCK ALERT: {item.name}")

            # 5. Log the dispatch
            dispatch_record = SupplyDispatch(
                region_id=region_id,
                item_id=item.id,
                quantity_dispatched=qty
            )
            db.add(dispatch_record)

            # Store the intended event payload
            successful_updates.append(
                InventoryUpdatedPayload(
                    item_id=item.id,
                    item_name=item.name,
                    quantity_deducted=qty,
                    new_stock=item.current_stock,
                    minimum_threshold=item.minimum_threshold,
                    unit=item.unit,
                    is_low_stock=is_low_stock
                )
            )

        # 6. Commit the database transaction FIRST
        await db.commit()

        # 7. Safely broadcast events ONLY if commit succeeds
        for payload in successful_updates:
            event = IntelligenceEvent(
                event_type=WSEventType.INVENTORY_UPDATED,
                region_id=region_id,
                source="logistics",
                payload=payload.model_dump()
            )
            try:
                # Durable publish to EventBus for backend consumers
                await EventBus.publish(event)
                
                # Direct publish to WebSocket clients
                await broadcast_ws_event(
                    event_type=WSEventType.INVENTORY_UPDATED,
                    payload=payload.model_dump(),
                    region_id=region_id,
                    correlation_id=event.event_id  # ensure unique event id
                )
            except Exception as e:
                # Do NOT rollback DB on publish failure, just log it.
                logger.error(f"Failed to publish INVENTORY_UPDATED event {event.event_id}: {str(e)}", exc_info=True)

        return response

