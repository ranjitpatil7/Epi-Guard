import asyncio
from app.db.redis import redis_manager
async def clean_redis():
    await redis_manager.connect()
    redis = redis_manager.get_client()
    await redis.delete('jalrakshak:events')
    print('Redis stream cleaned')

asyncio.run(clean_redis())
