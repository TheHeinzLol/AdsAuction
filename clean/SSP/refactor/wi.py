import asyncio
import logging

from dependencies.redis import close_redis, get_redis
from src.worker_insert import worker_insert

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s [%(funcName)s]:\n%(message)s",
)

logging.getLogger("src.worker_insert").setLevel(logging.INFO)

async def main():
    redis = await get_redis()
    await worker_insert(redis)
    await close_redis()

if __name__ == "__main__":
    asyncio.run(main())


