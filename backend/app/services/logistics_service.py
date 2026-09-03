import math
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.inventory_service import InventoryService

logger = logging.getLogger(__name__)

# Standard Emergency Kit deducted per region during dispatch
STANDARD_EMERGENCY_KIT: List[Tuple[str, int]] = [
    ("ORS Packets", 500),
    ("Water Purification Tablets", 1000),
    ("Vaccines (Cholera)", 200),
]


async def execute_dispatch(
    db: AsyncSession,
    target_region_ids: List[int],
    kit_overrides: Optional[Dict[int, List[Tuple[str, int]]]] = None
) -> Dict[str, Any]:
    """
    Execute a physical fleet dispatch:
    1. Calculate the optimal route (TSP).
    2. Deduct standard emergency kit inventory for each target region.
    3. Return the route + inventory warnings.
    """
    route_result = await calculate_optimal_route(db, target_region_ids)

    all_warnings: List[str] = []
    dispatched_regions: List[Dict[str, Any]] = []

    for region_id in target_region_ids:
        kit = STANDARD_EMERGENCY_KIT
        if kit_overrides and region_id in kit_overrides:
            kit = kit_overrides[region_id]

        inv_result = await InventoryService.deduct_stock(db, region_id, kit)
        if inv_result.get("warnings"):
            all_warnings.extend(inv_result["warnings"])

        dispatched_regions.append({
            "region_id": region_id,
            "kit": [{"item": name, "quantity": qty} for name, qty in kit],
            "status": "dispatched"
        })

    logger.info(f"Fleet dispatched to {len(target_region_ids)} regions. Warnings: {all_warnings}")

    return {
        **route_result,
        "dispatch_status": "completed",
        "dispatched_regions": dispatched_regions,
        "inventory_warnings": all_warnings,
    }

# The Command Hub is considered to be in Bhopal (central India)
COMMAND_HUB_COORDS = (23.2599, 77.4126)

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees).
    """
    R = 6371.0 # Earth radius in kilometers
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

async def calculate_optimal_route(db: AsyncSession, target_region_ids: List[int]) -> Dict[str, Any]:
    """
    Solves the Traveling Salesperson Problem (TSP) using a Nearest Neighbor Greedy approach.
    Calculates the optimal dispatch route starting from the Hub, visiting all target regions, 
    and returning to the Hub.
    """
    if not target_region_ids:
        return {"route": [], "total_distance_km": 0, "estimated_time_hrs": 0}
        
    # Fetch real region coordinates from PostGIS
    from sqlalchemy import select, func
    from app.models.domain import Region
    
    stmt = select(
        Region.id,
        Region.name,
        func.ST_Y(func.ST_Centroid(Region.geometry)).label('lat'),
        func.ST_X(func.ST_Centroid(Region.geometry)).label('lng')
    ).where(Region.id.in_(target_region_ids))
    
    result = await db.execute(stmt)
    region_data = {}
    
    for row in result.all():
        if row.lat is None or row.lng is None:
            raise ValueError(f"Region {row.id} ('{row.name}') has no valid geometry coordinates.")
        region_data[row.id] = {"name": row.name, "lat": row.lat, "lng": row.lng}
        
    missing = set(target_region_ids) - set(region_data.keys())
    if missing:
        raise ValueError(f"Invalid or missing region IDs provided: {list(missing)}")
        
    unvisited = set(target_region_ids)
    current_loc = COMMAND_HUB_COORDS
    
    route = [{"id": "HUB", "name": "Central Command Hub", "lat": current_loc[0], "lng": current_loc[1], "distance_from_last_km": 0}]
    total_distance = 0.0
    
    while unvisited:
        nearest_region = None
        min_dist = float('inf')
        
        for region_id in unvisited:
            coords = (region_data[region_id]["lat"], region_data[region_id]["lng"])
            dist = haversine(current_loc[0], current_loc[1], coords[0], coords[1])
            if dist < min_dist:
                min_dist = dist
                nearest_region = region_id
                
        # Move to nearest
        unvisited.remove(nearest_region)
        region_coords = (region_data[nearest_region]["lat"], region_data[nearest_region]["lng"])
        route.append({
            "id": nearest_region,
            "name": region_data[nearest_region]["name"],
            "lat": region_coords[0],
            "lng": region_coords[1],
            "distance_from_last_km": round(min_dist, 2)
        })
        total_distance += min_dist
        current_loc = region_coords
        
    # Return to Hub
    dist_to_hub = haversine(current_loc[0], current_loc[1], COMMAND_HUB_COORDS[0], COMMAND_HUB_COORDS[1])
    route.append({
        "id": "HUB",
        "name": "Central Command Hub (Return)",
        "lat": COMMAND_HUB_COORDS[0],
        "lng": COMMAND_HUB_COORDS[1],
        "distance_from_last_km": round(dist_to_hub, 2)
    })
    total_distance += dist_to_hub
    
    return {
        "route": route,
        "total_distance_km": round(total_distance, 2),
        "estimated_time_hrs": round(total_distance / 150.0, 2) # Assume drone speed 150km/h
    }
