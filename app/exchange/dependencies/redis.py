
from fastapi import FastAPI
from redis import asyncio as aioredis

_redis_client: Optional[aioredis.Redis] = None

async def get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = await aioredis.from_url(
                'redis://redis:6379',
                decode_responses=True
            )
    return _redis_client

async def close_redis():
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None

