from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.domain import Region, CommunityReport, WaterQualityRecord

class SpatialQueryService:
    """
    Service to execute PostGIS spatial queries using GeoAlchemy2 and SQLAlchemy 2.0.
    """
    
    @staticmethod
    async def get_reports_within_radius(db: AsyncSession, lon: float, lat: float, radius_meters: float = 5000):
        """
        Finds community reports within a specified radius (in meters) of a point.
        Uses ST_DWithin on geography types for accurate distance over earth's surface.
        """
        point_wkt = f"SRID=4326;POINT({lon} {lat})"
        # Cast to geography for accurate meter-based distance calculation
        stmt = select(CommunityReport).where(
            func.ST_DWithin(
                func.ST_GeographyFromText(func.ST_AsText(CommunityReport.location)),
                func.ST_GeographyFromText(point_wkt),
                radius_meters
            )
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_regions_containing_point(db: AsyncSession, lon: float, lat: float):
        """
        Finds regions whose polygons contain the given point.
        """
        point_wkt = f"SRID=4326;POINT({lon} {lat})"
        stmt = select(Region).where(
            func.ST_Contains(Region.geometry, func.ST_GeomFromEWKT(point_wkt))
        )
        result = await db.execute(stmt)
        return result.scalars().all()
