import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.domain import Region

async def run():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Region.id, Region.name))
        print(res.all())

asyncio.run(run())
