import asyncio
import json
import logging
import sys
from random import randint, random
from uuid import uuid4

from models.models import Base
from dependencies.redis import close_redis, get_redis
from dependencies.database import async_engine

from .examples import bid_ssp
from .examples import model_auctions_ssp_no_winner as mas

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s [%(funcName)s]:\n%(message)s",
)

async def main(
        pool_size: int=2500,
        mode: str="all",
        db_action: str="wipe",
        redis_action: str="wipe"
):

    if db_action == "wipe":
        await wipe_tables()

    redis = await get_redis()
    if redis_action == "wipe":
        await redis.flushall()

    await create_database_tables()

    if mode == "all":
        auctions = [{**mas, "auction_id": str(uuid4())} for _ in range(pool_size)]
        # introduce erroneous rows
        auctions[-1]["auction_id"] = auctions[0]["auction_id"]
        auctions[pool_size//2]["auction_id"] = auctions[0]["auction_id"]
        for _ in range(pool_size//10):
            auctions[randint(1,pool_size-1)]["auction_id"] = auctions[0]["auction_id"]
        for auction in auctions:
            auction_id = auction["auction_id"]
            bids=[{**bid_ssp, "auction_id_ssp": auction_id} for _ in range(3)]
            if random() < 0.1:
                bids[1]["auction_id_ssp"] = None
            await redis.xadd("auction:to_process", {
                "auction_data": json.dumps(auction),
                "bid_data": json.dumps(bids)
                })

    logger.debug(f"inserted {pool_size} aucs and their bids")
    logger.debug(f"example of auctions:\n{auction}")
    logger.debug(f"example of bid:\n{bids[0]}")
    await close_redis()

async def wipe_tables():
    from dependencies.database import SessionLocal
    from models.models import Auction, Bid, AuctionStage, BidStage
    from sqlalchemy import text
    async with SessionLocal() as session:
        stmt =  f"DROP TABLE IF EXISTS {Auction.__table__}, {Bid.__table__}, {AuctionStage.__table__}, {BidStage.__table__} CASCADE"
        await session.execute(text(stmt))
        await session.commit()

# Helper functions
async def create_database_tables():
    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

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

