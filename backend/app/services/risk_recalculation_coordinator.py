import asyncio
from datetime import datetime, timezone
import os
from typing import Dict, Any, Optional

class RiskRecalculationCoordinator:
    """
    Coordinates and coalesces risk recalculation events to prevent event storms.
    """
    _locks: Dict[int, asyncio.Lock] = {}
    _last_recalculation: Dict[int, datetime] = {}
    _pending_tasks: Dict[int, asyncio.Task] = {}
    
    # Configuration
    DEBOUNCE_SECONDS = float(os.getenv("RISK_RECALCULATION_DEBOUNCE_SECONDS", "5.0"))
    
    @classmethod
    def get_lock(cls, region_id: int) -> asyncio.Lock:
        if region_id not in cls._locks:
            cls._locks[region_id] = asyncio.Lock()
        return cls._locks[region_id]
        
    @classmethod
    async def schedule_recalculation(cls, region_id: int, event: Any, callback: Any, bypass_debounce: bool = False) -> bool:
        """
        Schedules a recalculation. If one is already pending for this region, it might be coalesced.
        If bypass_debounce is True (e.g. CRITICAL event), it executes immediately.
        Returns True if a new recalculation was triggered or scheduled, False if coalesced into an existing pending one.
        """
        if bypass_debounce:
            # Execute immediately, bypass coordination
            asyncio.create_task(callback(region_id, event))
            cls._last_recalculation[region_id] = datetime.now(timezone.utc)
            return True
            
        async with cls.get_lock(region_id):
            now = datetime.now(timezone.utc)
            last_recalc = cls._last_recalculation.get(region_id)
            
            # If we recalculated very recently, we need to debounce
            if last_recalc and (now - last_recalc).total_seconds() < cls.DEBOUNCE_SECONDS:
                # If there's already a pending task, coalesce this event into it
                if region_id in cls._pending_tasks and not cls._pending_tasks[region_id].done():
                    return False # Coalesced
                    
                # Schedule a new one after debounce
                wait_time = cls.DEBOUNCE_SECONDS - (now - last_recalc).total_seconds()
                cls._pending_tasks[region_id] = asyncio.create_task(cls._delayed_execution(region_id, event, callback, wait_time))
                return True
                
            else:
                # We haven't recalculated recently, do it now
                cls._pending_tasks[region_id] = asyncio.create_task(cls._immediate_execution(region_id, event, callback))
                return True
                
    @classmethod
    async def _immediate_execution(cls, region_id: int, event: Any, callback: Any):
        cls._last_recalculation[region_id] = datetime.now(timezone.utc)
        try:
            await callback(region_id, event)
        finally:
            if region_id in cls._pending_tasks:
                cls._pending_tasks.pop(region_id, None)
                
    @classmethod
    async def _delayed_execution(cls, region_id: int, event: Any, callback: Any, wait_time: float):
        await asyncio.sleep(wait_time)
        cls._last_recalculation[region_id] = datetime.now(timezone.utc)
        try:
            await callback(region_id, event)
        finally:
            if region_id in cls._pending_tasks:
                cls._pending_tasks.pop(region_id, None)

    @classmethod
    def reset_for_testing(cls):
        cls._locks.clear()
        cls._last_recalculation.clear()
        cls._pending_tasks.clear()
