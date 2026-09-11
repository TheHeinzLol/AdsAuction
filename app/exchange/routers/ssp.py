import aiohttp
import asyncio
import json
import logging
import time
import uuid

from datetime import datetime
from fastapi import APIRouter, Depends, Path, Request
from typing import Annotated

from app.exchange.schemas.schemas import SSPUserInfoSchema, SSPResponseSchema
from app.exchange.middleware.metrics import REQUESTS_BY_DEVICE, REQUESTS_BY_REGION

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

@router.post('/ad_request', response_model=SSPResponseSchema)
async def respond_to_ad_request(
        user_info: SSPUserInfoSchema,
        request: Request
        ):
    # Provide prometheus with data
    REQUESTS_BY_DEVICE.labels(device=user_info.device).inc()
    REQUESTS_BY_REGION.labels(region=user_info.region).inc()
    # convert info to dict
    user_info_json = user_info.model_dump()

    # create client
    try:
        redis = request.app.state.redis 
    except Exception as e:
        print(f'Failed to get redis client: {e}')

    # Get list of active DSPs
    if redis:
        dsp_list = list((await redis.hgetall("dsp:api_keys")).keys())
    else:
        raise ValueError("No redis instance is initiated")
        # or should I make a list of spare dsp urls for that case?
    # create a uuid for an auction
    auction_uuid = str(uuid.uuid4())
    # caching auction uuid for later bulk insert into database
    try:
        await redis.rpush("auction:to_process", auction_uuid)
    except Exception as e:
        print(f"\n=========================\nFailed to store auction uuid:\n{e}")

    # take timestamp of auction start
    time_auc_started = time.time()
    # make async bid requests to all DSPs
    tasks = [send_bid_request(redis, dsp, user_info_json) for dsp in dsp_list]
    responses = await asyncio.gather(*tasks)

    # collect valid bids
    bids = []
    for resp in responses:
        if resp.get("bid_amount") == -1 or resp.get("bid_amount") is None:
            continue
        else:
            bids.append(resp)

    # cache results in redis but send ad placeholder to the ssp
    # if no bids then no winner, no winning bid, no ads
    if not bids:
        user_info_json['ad_url'] = "no bids ad placeholder"
        auc_data = {
            "winner": "None",
            "winning_bid": -1,
            "creative_url": "no bids ad placeholder"
            }
    else:
        winner = max(bids, key=lambda b: b['bid_amount'])
        # mark bid as winning 
        winner["is_winning"] = True 
        user_info_json['ad_url'] = winner['creative_url']
        auc_data = {
            "winner": winner["dsp_id"],
            "winning_bid": winner["bid_amount"],
            "creative_url": winner["creative_url"]
            }

    # timestamp of auc ending
    time_auc_ended = time.time()

    # caching auction to redis
    auc_data.update({
            "time_created": time_auc_started,
            "time_closed": time_auc_ended,
            "user_context": json.dumps(user_info_json),
            })
    try:
        await redis.hset(f"auction:{auction_uuid}", mapping=auc_data)
    except Exception as e:
        print(f"\n=========================\nFailed to hset auction:\n{e}")

    # check if there are bids to cache and finish execution if there are none
    if len(bids) == 0:
        return SSPResponseSchema(**user_info_json)

    # chaching bids to redis
    try:
        for bid in bids:
            await redis.rpush(f"auction:{auction_uuid}:bids", json.dumps(bid))
    except Exception as e:
        print(f"\n=========================\nFailed to rpush bid {bid}:\n{e}")

    return SSPResponseSchema(**user_info_json)

async def send_bid_request(redis, dsp, user_info, timeout_ms=50) -> dict:
    if redis is None:
        api_key = "my_spare_key"
    else:
        api_key = await redis.hget('dsp:api_keys', dsp)
    timeout_seconds = timeout_ms / 1000.0
    url = f"http://dsp_fapi:8001/{dsp}"
    time_sent = time.time()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    url,
                    json=user_info,
                    headers={"X-API-Key": api_key},
                    #iohttp expects ClientTimeout instance instead of seconds
                    timeout=aiohttp.ClientTimeout(total=timeout_seconds)
                    ) as response:
                response_body = await response.json()
                time_received = time.time()
    except asyncio.TimeoutError:
        return {
                "dsp_id": dsp,
                "status": "timeout",
                "error": f"Request timed out after {timeout_seconds}s"
            }
    except aiohttp.ClientError as e:
        return {"dsp_id": dsp, "status": "client_error", "error": str(e)}
    except Exception as e:
        return {"dsp_id": dsp, "status": "unexpected_error", "error": str(e)}

    time_response = time_received - time_sent
    bid_data = {
            "dsp_id": dsp,
            "time_sent": time_sent,
            "time_received": time_received,
            "time_response": time_response,
            "bid_amount": response_body.get('bid_amount', -1),
            "creative_url": response_body.get('creative_url', 'No ad url provided'),
            "is_winning": False
            }
    return bid_data

