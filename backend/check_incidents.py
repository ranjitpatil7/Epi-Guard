import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.domain import IntelligenceIncident
async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(IntelligenceIncident.incident_id, IntelligenceIncident.incident_type, IntelligenceIncident.region_id, IntelligenceIncident.source_event_ids))
        for row in res:
            print(row[0], row[1], len(row[3]) if row[3] else 0)

asyncio.run(check())
