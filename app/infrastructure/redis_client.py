
import redis.asyncio as redis
import os

_redis = None

async def get_redis():
    global _redis
    if _redis is None:
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis = redis.from_url(url, decode_responses=True)
    return _redis
