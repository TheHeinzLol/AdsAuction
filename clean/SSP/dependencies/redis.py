
import os

from redis import asyncio as aioredis

_redis_client: aioredis.Redis | None = None
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = 6379
async def get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = await aioredis.from_url(
                f'redis://{REDIS_HOST}:{REDIS_PORT}',
                decode_responses=True
            )
    return _redis_client

async def close_redis():
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None

