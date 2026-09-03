import asyncio
from app.db.redis import redis_manager
async def check():
    await redis_manager.connect()
    redis = redis_manager.get_client()
    info = await redis.xinfo_stream('intelligence_events')
    print(info)

asyncio.run(check())
