import asyncio
import logging

from dependencies.redis import close_redis, get_redis
from src.worker_render import worker_render

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s [%(funcName)s]:\n%(message)s",
)

logging.getLogger("src.worker_render").setLevel(logging.INFO)

async def main():
    redis = await get_redis()
    await worker_render(redis)
    await close_redis()

if __name__ == "__main__":
    asyncio.run(main())


