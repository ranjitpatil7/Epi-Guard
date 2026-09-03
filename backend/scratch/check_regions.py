import asyncio
from app.db.session import SessionLocal
from app.models.domain import Region
from sqlalchemy import select

async def get():
    async with SessionLocal() as db:
        res = await db.execute(select(Region.id))
        return res.scalars().all()

print(asyncio.run(get()))
