import logging
from typing import List, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_Intersects, ST_Touches
from app.models.domain import Region

logger = logging.getLogger(__name__)

class SpatialCorrelationEngine:
    """
    Handles PostGIS spatial queries for event correlation.
    """
    
    @staticmethod
    async def get_neighboring_regions(db: AsyncSession, region_id: int) -> List[int]:
        """
        Returns a list of region_ids that physically touch or intersect the given region.
        """
        # First get the geometry of the target region
        stmt = select(Region.geometry).where(Region.id == region_id)
        result = await db.execute(stmt)
        target_geom = result.scalar_one_or_none()
        
        if target_geom is None:
            return []
            
        # Find intersecting or touching regions
        stmt = select(Region.id).where(
            and_(
                Region.id != region_id,
                func.ST_Intersects(Region.geometry, target_geom)
            )
        )
        result = await db.execute(stmt)
        return [row[0] for row in result.all()]
        
    @staticmethod
    async def get_regions_within_radius(db: AsyncSession, region_id: int, radius_meters: float) -> List[int]:
        """
        Returns regions within a specific distance (in meters) of the target region.
        Note: srid=4326 uses degrees by default for ST_DWithin unless cast to geography.
        We assume geography cast for meters.
        """
        stmt = select(Region.geometry).where(Region.id == region_id)
        result = await db.execute(stmt)
        target_geom = result.scalar_one_or_none()
        
        if target_geom is None:
            return []
            
        # Use ST_DWithin on geography for meters
        stmt = select(Region.id).where(
            and_(
                Region.id != region_id,
                func.ST_DWithin(func.Geography(Region.geometry), func.Geography(target_geom), radius_meters)
            )
        )
        result = await db.execute(stmt)
        return [row[0] for row in result.all()]

    @staticmethod
    async def are_regions_neighbors(db: AsyncSession, region_id_1: int, region_id_2: int) -> bool:
        """
        Checks if two regions are neighbors (touch or intersect).
        """
        if region_id_1 == region_id_2:
            return True
            
        stmt = select(func.ST_Intersects(
            select(Region.geometry).where(Region.id == region_id_1).scalar_subquery(),
            select(Region.geometry).where(Region.id == region_id_2).scalar_subquery()
        ))
        result = await db.execute(stmt)
        is_intersecting = result.scalar_one_or_none()
        return bool(is_intersecting)
