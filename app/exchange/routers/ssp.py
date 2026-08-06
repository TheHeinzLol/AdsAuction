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
    # take timestamp of auction start
    time_auc_started = time.time()
    # make async bid requests to all DSPs
    tasks = [send_bid_request(redis, dsp, user_info_json, auction_uuid) for dsp in dsp_list]
    responses = await asyncio.gather(*tasks)

    bids = []

    for resp in responses:
        if resp.get("bid_amount"):
            bids.append(resp)
        else:
            continue

    if not bids:
        # impossible bid to match Float field in db yet to know there was no bid
        user_info_json['bid_amount'] = -1.0
        user_info_json['ad_url'] = "ssp.py ad placeholder"
        user_info_json['dsp_id'] = "no dsp sent a bid"
        return SSPResponseSchema(**user_info_json)

    winner = max(bids, key=lambda b: b['bid_amount'])
    
    # timestamp of auc ending
    time_auc_ended = time.time()
    # mark bid as winning 
    winner["is_winning"] = True 
    # chaching bids to redis
    try:
        for bid in bids:
            await redis.rpush(f"auction:{auction_uuid}:bids", json.dumps(bid))
    except Exception as e:
        print(f"\n=========================\nFailed to hset bids {bid}:\n{e}")
    # caching auction to redis
    auc_data = {
                "winner": winner["dsp_id"],
                "winning_bid": winner["bid_amount"],
                "time_created": time_auc_started,
                "time_closed": time_auc_ended,
                "user_context": user_info_json
                }
    try:
        await redis.hset(f"auction:{auction_uuid}", mapping=auc_data)
    except Exception as e:
        print(f"\n=========================\nFailed to hset auction:\n{e}")

    user_info_json['bid_amount'] = winner['bid_amount'] 
    user_info_json['ad_url'] = winner['creative_url']
    user_info_json['dsp_id'] = winner['dsp_id'] 
    return SSPResponseSchema(**user_info_json)

async def send_bid_request(redis, dsp, user_info, auction_uuid, timeout_ms=50) -> dict:
    if redis is None:
        api_key = "my_spare_key"
    else:
        api_key = await redis.hget('dsp:api_keys', dsp)
    timeout_seconds = timeout_ms / 1000.0
    url = f"http://dsp_fapi:8001/{dsp}"
    time_sent = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.post(url,
                                json=user_info,
                                headers={"X-API-Key": api_key},
                                timeout=aiohttp.ClientTimeout(total=timeout_seconds)
                                ) as response:
            try:
                response_body = await response.text()
            except Exception as e:
                return {
                        auction_uuid: {
                            "dsp_id": dsp,
                            "status": "Request failed",
                            "error": str(e)
                        }
                    }
            time_received = time.time()
            response_body = json.loads(response_body)
            if response.status != 200:
                logger.debug(f"Failed to retrieve bid request response:\n {response_body}")
                return {
                        auction_uuid: {
                            "dsp_id": dsp,
                            "response_body": response_body
                        }
                    }
            time_response = time_received - time_sent
            
            bid_data = {
                        "auction_uuid": auction_uuid,
                        "dsp_id": dsp,
                        "time_sent": time_sent,
                        "time_received": time_received,
                        "time_response": time_response,
                        "bid_amount": response_body['bid_amount'],
                        "creative_url": response_body["creative_url"],
                        "is_winning": False
                }

            return bid_data
