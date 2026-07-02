import aiohttp
import asyncio
import json
import logging

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
    dsp_list = list((await redis.hgetall("dsp:api_keys")).keys())
    # make async bid requests to all DSPs
    tasks = [send_bid_request(redis, dsp, user_info_json) for dsp in dsp_list]
    responses = await asyncio.gather(*tasks)

    bids = []
    for resp in responses:
        if resp and resp.get("bid_amount"):
            bids.append(resp)
        else:
            continue

    if not bids:
        user_info_json['ad_url'] = "ssp.py ad placeholder"
        return SSPResponseSchema(**user_info_json)

    winner = max(bids, key=lambda b: b['bid_amount'])

    # ADD LOGGING HERE
    #=========
    #=========

    user_info_json['bid_amount'] = winner['bid_amount'] 
    user_info_json['ad_url'] = winner['creative_url']
    user_info_json['dsp_id'] = winner['dsp_id'] 
    return user_info_json

async def send_bid_request(redis, dsp, user_info, timeout_ms=50) -> dict:
    if redis is None:
        api_key = "my_spare_key"
    else:
        api_key = await redis.hget('dsp:api_keys', dsp)
    timeout_seconds = timeout_ms / 1000.0
    url = f"http://dsp_fapi:8001/{dsp}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url,
                                json=user_info,
                                headers={"X-API-Key": api_key},
                                timeout=aiohttp.ClientTimeout(total=timeout_seconds
                                                              )) as response:
            response_body = await response.text()
            response_body = json.loads(response_body)
            if response.status != 200:
                logger.debug(f"send_bid_request response: {response_body}")
            return response_body
