import json
from typing import Any, Optional
import redis.asyncio as redis

# Using a global redis connection pool for the app
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

class CacheService:
    """
    Redis caching service for expensive queries.
    """
    @staticmethod
    async def get_cached(key: str) -> Optional[Any]:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
        return None

    @staticmethod
    async def set_cached(key: str, value: Any, expire_seconds: int = 300):
        await redis_client.set(key, json.dumps(value), ex=expire_seconds)
