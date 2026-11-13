
import asyncio
import sqlalchemy
from fastapi import Request
from redis import asyncio as aioredis
import json
import time
import logging

from ..dependencies.database import SessionLocal
from ..models.models import Auction, Bid
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError

# del
from random import random
logger = logging.getLogger(__name__)

failed_rows = {
        "auctions": [],
        "bids": []
}

async def worker_insert(
        redis: aioredis.Redis,
        #rename to batch size
        batch_size: int = 2500,
        interval_sec: int = 2):
    try:
        logger.info("worker started")
        last_insert_time = time.time()
        while True:
            pending = await redis.llen("auction:to_process")
            time_since_last_insert = time.time() - last_insert_time
            #logger.debug(f"Time since last insert: {time_since_last_insert}, pending {pending}")
            if pending >= batch_size or time_since_last_insert >= interval_sec:
                aucs_to_insert = []
                bids_to_insert = []
                #get the records from redis
                auction_ids = await redis.lrange("auction:to_process", 0, batch_size - 1)
                logger.debug(f"=====auction_ids=====:\n{auction_ids}")
                if not auction_ids:
                    logger.debug(f"Continuing...")
                    continue
                for auction_id in auction_ids:
                    logger.debug(f"=====single auction_id=====:\n{auction_id}")
                    auction_data = await redis.lrange(f"auction:{auction_id}", 0, -1)
                    logger.debug(f"=====auction_data before loads=====:\n{auction_data}")
                    auction_data = json.loads(auction_data[0])
                    logger.debug(f"=====auction_data after json.loads()=====:\n{auction_data}")
                    aucs_to_insert.append(auction_data)
                    if random() < 0.02:
                        aucs_to_insert.append(auction_data)
                    # get bids
                    raw_bids = await redis.lrange(f"auction:{auction_id}:bids", 0, -1)
                    logger.debug(f"=====raw_bids=====:\n{raw_bids}")
                    bids = [json.loads(b) for b in raw_bids]
                    bids_to_insert.extend(bids)
                    logger.debug(f"bids: \n{bids}")
                    try:
                        logger.debug(f"=====Single bid=====:\n{bids[0]}")
                    except IndexError:
                        pass
                await bulk_insert(aucs_to_insert, bids_to_insert)
                try:
                    for auction_id in auction_ids:
                        await redis.delete(f"auction:{auction_id}")
                        await redis.delete(f"auction:{auction_id}:bids")
                    await redis.ltrim('auction:to_process', batch_size, -1)
                except Exception as e:
                    logger.error(f"Failed deleting:\n{str(e)}")
                logger.info("inserted rows")
                pending = await redis.llen("auction:to_process")
                logger.info(f"pending:{pending}")
                last_insert_time = time.time()
    except Exception as e:
        logger.error(f"Worker crashed: {e}")
        raise

async def bulk_insert(aucs: list[dict], bids: list[dict]):
    async with SessionLocal() as db:
        await insert_with_bisection(db, Auction, aucs)
        await insert_with_bisection(db, Bid, bids)
        logger.error(f"failed rows: {failed_rows}")

async def insert_with_bisection(db, table, data_batch):
    global failed_rows
    try:
        await db.execute(insert(table.__table__), data_batch)
        await db.commit()
    except Exception as e:
        await db.rollback()
        if len(data_batch) == 1:
            #logger.error(f"row insert failed:\n{e}")
            if table.__table__ == Auction.__table__:
                failed_rows["auctions"].append((data_batch[0], str(e)))
            elif table.__table__ == Bid.__table__:
                failed_rows["bids"].append((data_batch[0], str(e)))
            return
        # Split and retry
        mid = len(data_batch) // 2
        await insert_with_bisection(db, table, data_batch[:mid])
        await insert_with_bisection(db, table, data_batch[mid:])

