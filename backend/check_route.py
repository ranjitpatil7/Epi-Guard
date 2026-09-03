import asyncio
from app.db.session import AsyncSessionLocal
from app.services.logistics_service import calculate_optimal_route
async def test_route():
    async with AsyncSessionLocal() as db:
        res = await calculate_optimal_route(db, [1, 8])
        print(res)

asyncio.run(test_route())
