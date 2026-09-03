import asyncio
from sqlalchemy import select, func
from app.db.session import AsyncSessionLocal
from app.models.domain import Region
async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Region.id, Region.name).where(Region.geometry == None))
        print(res.all())

asyncio.run(check())
