from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict, Any
from app.db.session import get_db
from app.models.domain import Region
from app.services.cache_service import CacheService

router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
async def get_regions(db: AsyncSession = Depends(get_db)):
    """Get a list of all regions without heavy geometries."""
    cache_key = "api:regions:all"
    cached = await CacheService.get_cached(cache_key)
    if cached:
        return cached

    stmt = select(
        Region.id, 
        Region.name, 
        Region.state, 
        Region.district, 
        Region.population,
        func.ST_Y(func.ST_Centroid(Region.geometry)).label('lat'),
        func.ST_X(func.ST_Centroid(Region.geometry)).label('lng')
    )
    result = await db.execute(stmt)
    
    regions = []
    for row in result.all():
        regions.append({
            "id": row.id,
            "name": row.name,
            "state": row.state,
            "district": row.district,
            "population": row.population,
            "lat": row.lat,
            "lng": row.lng
        })
    
    await CacheService.set_cached(cache_key, regions, expire_seconds=3600)
    return regions

@router.get("/{region_id}", response_model=Dict[str, Any])
async def get_region(region_id: int, db: AsyncSession = Depends(get_db)):
    """Get detailed region info including GeoJSON geometry."""
    cache_key = f"api:regions:{region_id}"
    cached = await CacheService.get_cached(cache_key)
    if cached:
        return cached
        
    stmt = select(
        Region, 
        func.ST_AsGeoJSON(Region.geometry).label('geojson')
    ).where(Region.id == region_id)
    
    result = await db.execute(stmt)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Region not found")
        
    region, geojson_str = row
    
    import json
    data = {
        "id": region.id,
        "name": region.name,
        "state": region.state,
        "district": region.district,
        "population": region.population,
        "geometry": json.loads(geojson_str) if geojson_str else None
    }
    
    await CacheService.set_cached(cache_key, data, expire_seconds=3600)
    return data
