
import asyncio
import sqlalchemy
from fastapi import Request
from redis import asyncio as aioredis
import json
import time
import logging

logger = logging.getLogger(__name__)

async def bulk_insert(
        redis: aioredis.Redis,
        #rename to batch size
        batch_size: int = 2500,
        interval_sec: int = 2):
    try:
        logger.info("worker started")
        last_insert_time = time.time()
        while True:
            time.sleep(1)
            pending = await redis.llen("auction:to_process")
            time_since_last_insert = time.time() - last_insert_time
            logger.debug(f"Time since last insert: {time_since_last_insert}, pending {pending}")
            if pending >= batch_size or time_since_last_insert >= interval_sec:
                #get the records from redis
                auction_ids = await redis.lpop('auction:to_process', batch_size)
                logger.debug(f"auc ids: {auction_ids}")
                #in case it is time to insert but there are no auction records
                if not auction_ids:
                    logger.debug(f"Continuing...")
                    continue
                for auction_id in auction_ids:
                    auction_data = await redis.hgetall(f'auction:{auction_id}')
                    logger.debug(f"auction_dsta: \n{auction_data}")
                    # think if this is even possible. Leave for secure code?
                    if not auction_data:
                        continue
                    # get bids
                    bids_key = f"auction:{auction_id}:bids"
                    raw_bids = await redis.lrange(bids_key, 0, -1)
                    bids = [json.loads(b) for b in raw_bids]
                    logger.info("insert complete")
                    try:
                        await redis.delete(f"auction:{auction_id}")
                        await redis.delete(f"auction:{auction_id}:bids")
                    except Exception as e:
                        logger.error(f"Failed deleting:\n{str(e)}")
                #insert
                last_insert_time = time.time()
    except Exception as e:
        logger.error(f"Worker crashed: {e}", exc_info=True)
        raise


        # clean up
     #   await redis.delete(bids_key)

