from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.logistics_service import calculate_optimal_route, execute_dispatch
from app.db.session import get_db

router = APIRouter()


class DispatchRequest(BaseModel):
    region_ids: List[int]
    kit_overrides: Optional[Dict[int, List[List]]] = None  # {region_id: [["item_name", qty], ...]}


@router.get("/dispatch-route", response_model=Dict[str, Any])
async def get_dispatch_route(
    regions: str = Query(..., description="Comma separated list of region IDs (e.g. '1,3,5')"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Calculate the optimal TSP dispatch route for a fleet visiting the specified regions.
    """
    try:
        if not regions:
            raise ValueError("No regions provided.")
            
        # Parse regions
        region_ids = [int(r.strip()) for r in regions.split(",") if r.strip().isdigit()]
        
        if not region_ids:
            raise ValueError("Invalid region IDs provided.")
            
        route_data = await calculate_optimal_route(db, region_ids)
        
        return {
            "status": "success",
            "data": route_data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/dispatch", response_model=Dict[str, Any])
async def dispatch_fleet(request: DispatchRequest, db: AsyncSession = Depends(get_db)):
    """
    Dispatch a fleet to the specified regions. Deducts standard emergency kits
    from the central inventory for each region.
    """
    try:
        if not request.region_ids:
            raise ValueError("No region IDs provided for dispatch.")

        # Convert kit_overrides from JSON-safe format to tuples
        overrides = None
        if request.kit_overrides:
            overrides = {
                rid: [(item[0], int(item[1])) for item in items]
                for rid, items in request.kit_overrides.items()
            }

        result = await execute_dispatch(db, request.region_ids, overrides)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
