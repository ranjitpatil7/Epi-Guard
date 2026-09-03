import asyncio
from sqlalchemy import select, update, func
from app.db.session import AsyncSessionLocal
from app.models.domain import Region
async def fix_region():
    async with AsyncSessionLocal() as db:
        stmt = update(Region).where(Region.id == 8).values(geometry=func.ST_GeomFromText('POLYGON((92 24,93 24,93 25,92 25,92 24))', 4326))
        await db.execute(stmt)
        await db.commit()
        print('Fixed Region 8')

asyncio.run(fix_region())
