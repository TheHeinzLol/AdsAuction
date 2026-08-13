import asyncio
import sqlalchemy
from fastapi import Request

async def bulk_insert(
        request: Request
        records_limit: int = 2500):

    #get redis from app state
    try:
        redis = request.app.state.redis
    except Exception as e:
        print(f"===============Failed to  get redis from fastapi state:\n{e}")

    # get list of uuids to insert
    auction_ids = []
    
    for _ in range(records_limit):
        auction_id = await redis.lpop("auction:to_process")
        if not aucton_id:
            break
        auction_ids.append(auction_id)
    
    if not auction_ids:
        return
    
    #process all auctions
    for auction_id in auction_ids:
        auction_data = await redis.hget(f"auction:{auction_id}")
        if not auction_data:
            continue

        bids_key = f"auction:{auction_id}:bids"
        raw_bids = await redis.lrange(bids_key, 0, -1)
        bids = [json.loads(b) for b in raw_bids]

    # insert here
    pass
    # clean up
    await redis.delete(f"auction:{auction_id}")
    await redis.delete(bids_key)

