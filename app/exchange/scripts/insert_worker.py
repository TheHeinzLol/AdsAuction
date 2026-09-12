import asyncio
import sqlalchemy
from fastapi import Request
from redis import asyncio as aioredis
import time
async def bulk_insert(
        redis: aioredis.Redis,
        #rename to batch size
        records_limit: int = 2500,
        batch_size: int = 2):
    last_insert_time = time.time()
    while True:
        pending = await redis.llen("auction:to_process")
        time_since_last_insert = time.time() - last_insert_time
        if pending >= batch_size or time_since_last_insert >= interval_sec:
            #get the records from redis
            auction_ids = await redis.lpop('auction:to_process', batch_size)
            #in case it is time to insert but there are no auction records
            if not auction_ids:
                continue
            for auction_id in auction_ids:
                auction_data = await redis.hgetall(f'auction:{auction_id}', )
                # think if this is even possible. Leave for secure code?
                if not auction_data:
                    continue
                # get bids
                bids_key = f"auction:{auction_id}:bids"
                raw_bids = await redis.lrange(bids_key, 0, -1)
                print(f'worker raw_bids: {raw_bids}')
                print(f"\n===============\nRAW BIDS==========\n{raw_bids[0]}\n=========type======\n{type(bids[0])}")
                bids = [json.loads(b) for b in raw_bids]
                print(f"\n===============\nBIDS==========\n{bids[0]}\n=========type======\n{type(bids[0])}")
#                await redis.delete(f"auction:{auction_id}")
            #insert
                last_insert_time = time.time()
        print("while end")


# draft end=========

    # clean up
 #   await redis.delete(bids_key)

