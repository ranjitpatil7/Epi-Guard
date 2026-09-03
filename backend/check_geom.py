import asyncio
from sqlalchemy import select, func
from app.db.session import AsyncSessionLocal
from app.models.domain import Region
async def test_route():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Region.id, Region.name, func.ST_AsText(Region.geometry)).where(Region.id.in_([1, 8])))
        print(res.all())

asyncio.run(test_route())
