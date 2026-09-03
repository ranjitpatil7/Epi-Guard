import logging
import asyncio
from typing import Optional
from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import ConnectionError, TimeoutError
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisManager:
    """
    Manages the async Redis connection pool.
    Implements health checks, bounded retries, and graceful degradation.
    """
    def __init__(self):
        self.pool: Optional[ConnectionPool] = None
        self._redis: Optional[Redis] = None

    async def connect(self):
        """Initializes the Redis connection pool."""
        if not self.pool:
            logger.info("Initializing Redis connection pool...")
            # We use the redis URL from settings, which defaults to the Docker compose service
            redis_url = settings.REDIS_URL if hasattr(settings, "REDIS_URL") else "redis://redis:6379/0"
            self.pool = ConnectionPool.from_url(
                redis_url,
                max_connections=50,
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
                retry_on_timeout=True
            )
            self._redis = Redis(connection_pool=self.pool)
            
            # Verify connection
            await self.ping(retries=3)

    async def disconnect(self):
        """Closes all connections in the pool gracefully."""
        if self._redis:
            logger.info("Closing Redis connection pool...")
            await self._redis.aclose()
            self._redis = None
            self.pool = None

    def get_client(self) -> Redis:
        """Returns the active Redis client."""
        if not self._redis:
            raise RuntimeError("Redis client is not initialized. Call connect() first.")
        return self._redis

    async def ping(self, retries: int = 1) -> bool:
        """Health check with optional bounded retries."""
        if not self._redis:
            return False
            
        for attempt in range(1, retries + 1):
            try:
                pong = await self._redis.ping()
                return pong
            except (ConnectionError, TimeoutError) as e:
                logger.warning(f"Redis ping failed (attempt {attempt}/{retries}): {str(e)}")
                if attempt < retries:
                    await asyncio.sleep(1.0 * attempt) # Exponential-ish backoff
        
        logger.error("Redis ping failed after all retries.")
        return False

# Global instance
redis_manager = RedisManager()
