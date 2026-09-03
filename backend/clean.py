import asyncio
from sqlalchemy import text
from app.db.session import AsyncSessionLocal
async def clean():
    async with AsyncSessionLocal() as db:
        await db.execute(text('DELETE FROM intelligence_incidents'))
        await db.commit()
        print('Cleaned')

asyncio.run(clean())
