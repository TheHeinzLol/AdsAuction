import asyncio
import json
import logging
from uuid import uuid4

from dependencies.redis import close_redis, get_redis

from .examples import model_auctions_ssp_no_winner as mas
from .examples import bid_ssp

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s [%(funcName)s]:\n%(message)s",
)

async def main(pool_size=2500,):
    redis = await get_redis()
    await redis.flushall()
    auctions = [{**mas, "auction_id": str(uuid4())} for _ in range(2500)]
    for auction in auctions:
        auction_id = auction["auction_id"]
        bids=[{**bid_ssp, "auction_id_ssp": auction_id}]
        async with redis.pipeline() as pipe:
            for bid in bids:
                pipe.rpush(f"auction:{auction_id}:bids", json.dumps(bid))
            pipe.rpush(f"auction:{auction_id}", json.dumps(auction))
            pipe.rpush("auction:to_process", auction_id)
            pipe.rpush("auction:to_render", auction_id)
            await pipe.execute()
    logger.debug(f"inserted {pool_size} aucs and their bids")
    logger.debug(f"example of auction:\n{auction}")
    logger.debug(f"example of bid:\n{bid}")
    await close_redis()

if __name__ == "__main__":
    asyncio.run(main())
