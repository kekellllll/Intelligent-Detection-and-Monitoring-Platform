"""Redis service for message queuing and caching."""
import json
from typing import Any, Optional
import redis.asyncio as redis
import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)


class RedisService:
    """Redis service for message queuing and caching."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.settings = get_settings()
    
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.redis_client = redis.from_url(
                self.settings.REDIS_URL,
                db=self.settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
    
    async def publish_sensor_data(self, channel: str, data: dict) -> None:
        """Publish sensor data to Redis channel."""
        if not self.redis_client:
            await self.connect()
        
        try:
            message = json.dumps(data)
            await self.redis_client.publish(channel, message)
            logger.debug(f"Published sensor data to channel {channel}")
        except Exception as e:
            logger.error(f"Failed to publish sensor data: {e}")
            raise
    
    async def subscribe_to_channel(self, channel: str):
        """Subscribe to Redis channel."""
        if not self.redis_client:
            await self.connect()
        
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe(channel)
        return pubsub
    
    async def cache_set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set value in cache with TTL."""
        if not self.redis_client:
            await self.connect()
        
        try:
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            await self.redis_client.setex(key, ttl, serialized_value)
            logger.debug(f"Cached value for key {key}")
        except Exception as e:
            logger.error(f"Failed to cache value: {e}")
            raise
    
    async def cache_get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis_client:
            await self.connect()
        
        try:
            value = await self.redis_client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Failed to get cached value: {e}")
            return None
    
    async def cache_delete(self, key: str) -> None:
        """Delete value from cache."""
        if not self.redis_client:
            await self.connect()
        
        try:
            await self.redis_client.delete(key)
            logger.debug(f"Deleted cached value for key {key}")
        except Exception as e:
            logger.error(f"Failed to delete cached value: {e}")


# Global Redis service instance
redis_service = RedisService()