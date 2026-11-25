import sys
import asyncio
import json
import logging
from random import random
from uuid import uuid4

from dependencies.redis import close_redis, get_redis

from .examples import model_auctions_ssp_no_winner as mas
from .examples import bid_ssp

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s [%(funcName)s]:\n%(message)s",
)

async def main(pool_size: int=2500, mode: str="happy", db_action: str="ignore", redis_action: str="ignore"):    
    if db_action == "wipe":
        await wipe_tables()

    redis = await get_redis()
    if redis_action == "wipe":
        await redis.flushall()
    if mode == "happy":
        auctions = [{**mas, "auction_id": str(uuid4())} for _ in range(pool_size)]
        for auction in auctions:
            auction_id = auction["auction_id"]
            bids=[{**bid_ssp, "auction_id_ssp": auction_id} for _ in range(3)]
            async with redis.pipeline() as pipe:
                for bid in bids:
                    pipe.rpush(f"auction:{auction_id}:bids", json.dumps(bid))
                pipe.rpush(f"auction:{auction_id}", json.dumps(auction))
                pipe.rpush("auction:to_process", auction_id)
                pipe.rpush("auction:to_render", auction_id)
                await pipe.execute()

    if mode == "fatal_aucs":
        auctions = [{**mas, "auction_id": str(uuid4())} for _ in range(pool_size)]
        # introduce erroneous rows
        auctions[-1]["auction_id"] = auctions[0]["auction_id"]
        auctions[pool_size//2]["auction_id"] = auctions[0]["auction_id"]
        for auction in auctions:
            auction_id = auction["auction_id"]
            bids=[{**bid_ssp, "auction_id_ssp": auction_id} for _ in range(3)]
            async with redis.pipeline() as pipe:
                for bid in bids:
                    pipe.rpush(f"auction:{auction_id}:bids", json.dumps(bid))
                pipe.rpush(f"auction:{auction_id}", json.dumps(auction))
                pipe.rpush("auction:to_process", auction_id)
                pipe.rpush("auction:to_render", auction_id)
                await pipe.execute()

    if mode == "fatal_bids":
        auctions = [{**mas, "auction_id": str(uuid4())} for _ in range(pool_size)]
        for auction in auctions:
            auction_id = auction["auction_id"]
            bids=[{**bid_ssp, "auction_id_ssp": auction_id} for _ in range(3)]
            if random() < 0.1:
                bids[1]["auction_id_ssp"] = None
            async with redis.pipeline() as pipe:
                for bid in bids:
                    pipe.rpush(f"auction:{auction_id}:bids", json.dumps(bid))
                pipe.rpush(f"auction:{auction_id}", json.dumps(auction))
                pipe.rpush("auction:to_process", auction_id)
                pipe.rpush("auction:to_render", auction_id)
                await pipe.execute()

    if mode == "fatal_render":
        auctions = [{**mas, "auction_id": str(uuid4())} for _ in range(pool_size)]
        for auction in auctions:
            auction_id = auction["auction_id"]
            bids=[{**bid_ssp, "auction_id_ssp": auction_id} for _ in range(3)]
            async with redis.pipeline() as pipe:
                for bid in bids:
                    pipe.rpush(f"auction:{auction_id}:bids", json.dumps(bid))
                pipe.rpush(f"auction:{auction_id}", json.dumps(auction))
                pipe.rpush("auction:to_process", auction_id)
                pipe.rpush("auction:to_render", auction_id)
                if random() < 0.1:
                    await redis.rpush("auction:to_render", str(uuid4()))
                await pipe.execute()

    if mode == "fill_render":
        auction_ids = await redis.lrange("auction:to_render", 0, pool_size)
        auctions = [{**mas, "auction_id": auction_id} for auction_id in auction_ids]
        for auction in auctions:
            auction_id = auction["auction_id"]
            async with redis.pipeline() as pipe:
                pipe.rpush(f"auction:{auction_id}", json.dumps(auction))
                pipe.rpush("auction:to_process", auction_id)
                pipe.rpush("auction:to_render", auction_id)
                await pipe.execute()
        logger.info("filled in  missing aucs")
        await close_redis()
        return

    if mode == "all":
        auctions = [{**mas, "auction_id": str(uuid4())} for _ in range(pool_size)]
        # introduce erroneous rows
        auctions[-1]["auction_id"] = auctions[0]["auction_id"]
        auctions[pool_size//2]["auction_id"] = auctions[0]["auction_id"]
        for _ in range(pool_size//10):
            auctions[randint(1,pool_size)]["auction_id"] = auctions[0]["auction_id"]
        for auction in auctions:
            auction_id = auction["auction_id"]
            bids=[{**bid_ssp, "auction_id_ssp": auction_id} for _ in range(3)]
            if random() < 0.1:
                bids[1]["auction_id_ssp"] = None
            async with redis.pipeline() as pipe:
                for bid in bids:
                    pipe.rpush(f"auction:{auction_id}:bids", json.dumps(bid))
                pipe.rpush(f"auction:{auction_id}", json.dumps(auction))
                pipe.rpush("auction:to_process", auction_id)
                pipe.rpush("auction:to_render", auction_id)
                if random() < 0.1:
                    await redis.rpush("auction:to_render", str(uuid4()))
                await pipe.execute()


    logger.debug(f"inserted {pool_size} aucs and their bids")
    logger.debug(f"example of auctions:\n{auction}")
    logger.debug(f"example of bid:\n{bid}")
    await close_redis()

    

async def wipe_tables():
    from dependencies.database import SessionLocal
    from sqlalchemy import text
    from models.models import Auction, Bid
    async with SessionLocal() as session:
        # TRUNCATE ... CASCADE ignores FK constraints entirely
        await session.execute(text(
            f"TRUNCATE TABLE {Auction.__table__}, {Bid.__table__} RESTART IDENTITY CASCADE"
        ))
        await session.commit()

if __name__ == "__main__":
    pool_size = int(sys.argv[1])
    mode = sys.argv[2]
    db_action = sys.argv[3] 
    redis_action = sys.argv[4]

    asyncio.run(main(
        pool_size=pool_size,
        mode=mode,
        db_action=db_action,
        redis_action=redis_action,
        )
    )
