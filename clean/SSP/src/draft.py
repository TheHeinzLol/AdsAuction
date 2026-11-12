
from ..dependencies.redis import close_redis, get_redis


import asyncio
import sqlalchemy
from fastapi import Request
from redis import asyncio as aioredis
import time
import json
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s [%(funcName)s]: %(message)s",
)


async def populate(redis):
    for i in range(10):
        auction_id =  str(uuid4())
        db_insert = {
                'auction_id': auction_id,
                'time_created': 1794409542.028402,
                'time_closed': 1794409542.041354,
                'publisher_id': 'pub_espn',
                'winner': 'adx_1',
                'winner_bid': 4.29,
                'is_rendered': 0
        }
        bid = {
                 'auction_id': auction_id,
                 'time_sent': 1794410584.936931,
                 'time_received': 1794410584.947893,
                 'adx_id': 'adx_1',
                 'creative_url': 'asstwat',
                 'bid_amount': 2.71,
                 'categories': ['sports', 'food', 'porn'],
                 'is_winning': True
        }
        try:
            await redis.rpush("auction:to_process", auction_id)
        except Exception as e:
            logger.error(f"failed to rpush:\n{e}")
        try:
            await redis.hset(f"auction:{auction_id}", mapping=db_insert)
        except Exception as e:
            logger.error(f"failed to hset:\n{e}")
        try:
            await redis.rpush(f"auction:{auction_id}:bids", json.dumps(bid))
        except Exception as e:
            logger.error(f"failed to rpush bid:\n{e}")

    pending = await redis.llen("auction:to_process")
    logger.info(f"redis populated. Current pool={pending}")

async def action(redis):
    batch_size = 200
    auction_ids = await redis.lpop('auction:to_process', batch_size)
    auction_ids = await redis.lpop('auction:to_process', batch_size)
    logger.debug(f"auction_ids:\n{auction_ids}")
    for auction_id in auction_ids:

        auction_data = await redis.hgetall(f'auction:{auction_id}')
        logger.debug(f"auction data:\n{auction_data}")
        
        bids_key = f"auction:{auction_id}:bids"
        logger.debug(f"bids key:\n{bids_key}")
        
        raw_bids = await redis.lrange(bids_key, 0, -1)
        logger.debug(f'raw_bids: {raw_bids}')
        logger.debug(f"\n===============RAW BID==========\n{raw_bids[0]}\n=========type======\n{type(raw_bids[0])}")
        
        bids = [json.loads(b) for b in raw_bids]
        logger.debug(f"bids:\n{bids}")
        logger.debug(f"\n===============BID==========\n{bids[0]}\n=========type======\n{type(bids[0])}")
#        await redis.delete(f"auction:{auction_id}")
async def main():
    redis = await get_redis()
    await redis.flushall()
    await populate(redis)
    #await action(redis)
if __name__ == "__main__":
    asyncio.run(main())
    
