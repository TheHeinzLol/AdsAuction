
from ..dependencies.redis import  get_redis


import asyncio
import sqlalchemy
from redis import asyncio as aioredis
import json
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s [%(funcName)s]: %(message)s",
)


async def populate(redis):
    for i in range(735):
        auction_id =  str(uuid4())
        db_insert = {
                'auction_id': auction_id,
                'time_created': 1794409542.028402,
                'time_closed': 1794409542.041354,
                'publisher_id': 'pub_espn',
                'winner': 'adx_1',
                'winner_bid': 4.29,
                'is_rendered': False
        }

        try:
            await redis.rpush("auction:to_process", auction_id)
        except Exception as e:
            logger.error(f"failed to rpush:\n{e}")
        try:
            await redis.rpush(f"auction:{auction_id}", json.dumps(db_insert))
        except Exception as e:
            logger.error(f"failed to hset:\n{e}")
        try:
            for b in range(3):
                bid = {
                     'auction_id': auction_id,
                     'time_sent': 1794410584.936931,
                     'time_received': 1794410584.947893,
                     'adx_id': f'adx_{b}',
                     'creative_url': 'asstwat',
                     'bid_amount': 2.71,
                     'categories': ['sports', 'food', 'porn'],
                     'is_winning': True
                }
                await redis.rpush(f"auction:{auction_id}:bids", json.dumps(bid))
        except Exception as e:
            logger.error(f"failed to rpush bid:\n{e}")

    pending = await redis.llen("auction:to_process")
    logger.info(f"redis populated. Current pool={pending}")

async def create_database_tables():
    from ..dependencies.database import async_engine
    from ..models.models import Base

    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

async def get_inserts(
        redis: aioredis.Redis,
        #rename to batch size
        batch_size: int = 2,
        ):
    try:
        while True:
            pending = await redis.llen("auction:to_process")
            logger.debug(f"current pending: {pending}")
            aucs_to_insert = []
            bids_to_insert = []
            #get the records from redis
            auction_ids = await redis.lrange('auction:to_process', 0, batch_size-1)
            logger.info(f"auc ids: {auction_ids}")
            for auction_id in auction_ids:
                logger.debug(f"auction id single: {auction_id}")
                auction_data = await redis.lrange(f'auction:{auction_id}', 0, -1)# TODO why empty while key present?
                logger.debug(f"auction_data before loads: \n{auction_data}")
                auction_data = json.loads(auction_data[0])
                logger.debug(f"auction_data: \n{auction_data}")
                aucs_to_insert.append(auction_data)
                # get bids
                raw_bids = await redis.lrange(f"auction:{auction_id}:bids", 0, -1)
                logger.debug(f"raw_bids: \n{raw_bids}")
                bids = [json.loads(b) for b in raw_bids]
                bids_to_insert.extend(bids)
                logger.debug(f"bids: \n{bids}")
                try:
                    logger.debug(f"a single bid: \n{bids[0]}")
                except IndexError:
                    pass
            #await bulk_insert(aucs_to_insert, bids_to_insert)

            try:
                for auction_id in auction_ids:
                    logger.info("Deleting")
                    await redis.delete(f"auction:{auction_id}")
                    await redis.delete(f"auction:{auction_id}:bids")
                full_pending = await redis.lrange('auction:to_process', 0, pending)
                logger.info(f"Trimming. Before trim:\n{full_pending}")
                await redis.ltrim('auction:to_process', batch_size, -1)
                full_pending = await redis.lrange('auction:to_process', 0, pending)
                logger.info(f"After trim:\n{full_pending}")
            except Exception as e:
                logger.error(f"Failed deleting:\n{str(e)}")
    except Exception as e:
        logger.error(f"Worker crashed: {e}")
        logger.error(f"pending: {pending}")
        logger.error(f"auction_ids: {auction_ids}")
        logger.error(f"auction_id: {auction_id}")
        logger.error(f"auction_data: {auction_data}")
        raise

failed_rows = []
async def insert_with_bisection(db, table, data_batch):
    global failed_rows
    try:
        await db.execute(insert(table), data_batch)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        if len(data_batch) == 1:
            # Single bad row isolated
            failed_rows.append(data_batch[0])
            return
        # Split and retry
        mid = len(data_batch) // 2
        await insert_with_bisection(db, table, data_batch[:mid])
        await insert_with_bisection(db, table, data_batch[mid:])

from ..dependencies.database import SessionLocal
from ..models.models import Auction, Bid
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError
async def bulk_insert(aucs, bids):

    async with SessionLocal() as db:
        await insert_with_bisection(db, Auction, aucs)
        await insert_with_bisection(db, Bid, bids)
#        try:
#            await db.execute(insert(Auction.__table__), aucs)
#            await db.commit()
#        except Exception as e:
#            await db.rollback()
#            logger.error(f"Failed the insert:\n{e}")
#            return {"insert failed": e}
#        try:
#            await db.execute(insert(Bid.__table__), bids)
#            await db.commit()
#        except Exception as e:
#            await db.rollback()
#            logger.error(f"Failed the insert:\n{e}")
#            return {"insert failed": e}
#
async def main():
    await create_database_tables()
    redis = await get_redis()
    await redis.flushall()
    await populate(redis)
#    await get_inserts(redis)
if __name__ == "__main__":
    asyncio.run(main())
    
