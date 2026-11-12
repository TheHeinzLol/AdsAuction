
import os
from fastapi import FastAPI
from redis import asyncio as aioredis
from typing import Optional

_redis_client: Optional[aioredis.Redis] = None
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6380")
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

