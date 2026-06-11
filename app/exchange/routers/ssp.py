import json

from datetime import datetime
from fastapi import APIRouter, Path
from typing import Annotated

from app.exchange.schemas.schemas import SSPUserInfoSchema, SSPResponseSchema
from app.exchange.middleware.metrics import REQUESTS_BY_DEVICE, REQUESTS_BY_REGION
router = APIRouter()

@router.get('/SSP/{id}')
async def respond_ssp(id: int):
        return {
                'id': id,
                'ad_url': f"http://localhost:8000/SSP/{id}",
                'date_shown': datetime.utcnow()
                }

# Redis client !!! Inject Later !!!
import aiohttp
import asyncio
from redis import asyncio as aioredis
redis_client = None

DSP_ENDPOINTS = [
        {
            "dsp_id": "dsp_1",
            "url": "http://dsp_fapi:8001/bid_request",
            "api_key": "key_1"
        }
]

async def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = await aioredis.from_url('redis://redis:6379', decode_responses=True)
    return redis_client


@router.post('/ad_request', response_model=SSPResponseSchema)
async def respond_to_ad_request(user_info: SSPUserInfoSchema):
    # Provide prometheus with data
    REQUESTS_BY_DEVICE.labels(device=user_info.device).inc()
    REQUESTS_BY_REGION.labels(region=user_info.region).inc()
    # convert info to dict
    user_info_json = user_info.model_dump()
    

    # create client 
    try:
        redis = await get_redis()
    except Exception as e:
        print('Failed to get redis client: ', e)

    # Get list of active DSPs
    dsp_list = await redis.get('dsp_list')
    # make async bid requests to all DSPs
    if not dsp_list:
        dsp_list = DSP_ENDPOINTS
    tasks = [send_bid_request(dsp, user_info_json) for dsp in dsp_list]
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

    user_info_json['ad_url'] = winner['creative_url']
    return user_info_json

async def send_bid_request(dsp, user_info) -> dict:
    url = dsp['url']
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=user_info) as response:
            response_body = await response.text()
            response_body = json.loads(response_body)
            if response.status != 200:
                logger.debug(f"send_bid_request response: {response_body}")
            return response_body
