
import asyncio
import logging
import time

from dependencies.database import SessionLocal
from models.models import Auction
from redis import asyncio as aioredis
from sqlalchemy import select, update

logger = logging.getLogger(__name__)

failed_rows =[]

async def worker_render(
        redis: aioredis.Redis,
        batch_size: int = 2500,
        interval_sec: int = 2
):
    if redis is None:
        return
    logger.info("Worker started")
    last_update_time = time.time()
    try:
        while True:
            pending = await redis.llen("auction:to_render")
            time_since_last_update = time.time() - last_update_time
            if pending >= batch_size or time_since_last_update >= interval_sec:
                auction_ids = await redis.lpop("auction:to_render",  batch_size)
                if not auction_ids:
                    await asyncio.sleep(0.1)
                    continue
                await bulk_update(auction_ids, redis)
                logger.info("updated rows")
                last_update_time = time.time()
    except asyncio.CancelledError:
        raise  # Let graceful shutdown work
    except Exception as e:
        logger.error(f"Worker crashed: {e}")
        await asyncio.sleep(1)
       

async def bulk_update(aucs: list[str], redis: aioredis.Redis):
    matched = []
    unmatched = []
    async with SessionLocal() as db:
        # get only existing rows since update doesn't throw an error
        # so we could lose those renders not yet having an auction inserted
        existing = await db.scalars(select(Auction.auction_id).where(Auction.auction_id.in_(aucs)))
        existing = set(existing.all())
        for auc in aucs:
            if auc in existing:
                matched.append(auc)
            else:
                unmatched.append(auc)
        #update itself
        await update_with_bisection(db, Auction, matched)
        if failed_rows:
            logger.error(f"failed rows: {failed_rows}")
            try:
                await redis.rpush("auction:to_render", redis.rpush(*unmatched))
                failed_rows.clear() 
            except Exception as e:
                logger.error(f"Failed to rpush failed rows:\n{e}")

async def update_with_bisection(db, table, auctions):
    stmt = update(table).where(table.auction_id.in_(auctions)).values(is_rendered=True)
    try:
        await db.execute(stmt)
        await db.commit()
        logger.debug(f"Updated {len(auctions)} rows")
    except Exception as e:
        await db.rollback()
        if len(auctions) == 1:
            failed_rows.append((auctions[0], str(e)))
            return
        # Split and retry
        mid = len(auctions) // 2
        await update_with_bisection(db, table, auctions[:mid])
        await update_with_bisection(db, table, auctions[mid:])



