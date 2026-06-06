from datetime import datetime
from fastapi import APIRouter, Path
from typing import Annotated

from ..schemas.schemas import SSPUserInfoSchema, SSPResponseSchema
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
            "url": "http:/localhost:8001/bid_request",
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
    # convert info to dict
    user_info_json = user_info.model_dump()
    # create client 
    try:
        redis = await get_redis()
    except Exception as e:
        print('Failed to get redis client: ', e)
    # get dsp from redis or use hardcoded
    dsp_list = await redis.get("active_dsps")
    if dsp_list:
        import json
        dsp_configs = json.loads(dsp_list)
    else:
        dsp_configs = DSP_ENDPOINTS
    #send parallel bid requests
    async with aiohttp.ClientSession() as session:
        tasks = []
        for dsp in dsp_configs:
            task = send_bid_request(session, dsp, user_info_json)
            tasks.append(task)
        responses = await asyncio.gather(*tasks, return_exceptions=True)
    #parse valid bids
    bids = []
    for response in responses:
        if isinstance(response, Exception):
            continue
        if response and response.get("bid_amount"):
            bids.append(response)
    # select winner
    if not bids:
        user_info_json['ad_url'] = "placeholder_creative_url"
        return SSPResponseSchema(**user_info_json)
    winner = max(bids, key=lambda b: b["bid_amount"])
    # log the winner
    asyncio.create_task(log_auction_result(user_info_json, winner))
    # add url to send back to user
    user_info_json['ad_url'] = winner['creative_url']
    return SSPResponseSchema(**user_info_json)

from typing import List, Dict, Any
async def send_bid_request(
        session: aiohttp.ClientSession,
        dsp: Dict[str, Any],
        user_info: Dict[str, Any]
) -> Dict[str, Any]:
    """Send bid request to a single DSP."""
    try:
        async with session.post(
            dsp["url"],
            json=user_info,
            headers={"X-API-Key": dsp["api_key"]},
            timeout=aiohttp.ClientTimeout(total=0.05)  # 50ms timeout
        ) as response:
            if response.status == 200:
                result = await response.json()
                return {
                    "dsp_id": dsp["id"],
                    "bidder_id": result.get("bidder_id", "unknown"),
                    "bid": result.get("bid", 0),
                    "creative_url": result.get("creative_url", "")
                }
            else:
                return None
    except Exception as e:
        # Log error but don't break the auction
        print(f"DSP {dsp['id']} failed: {e}")
        return None

async def log_auction_result(user_info: Dict[str, Any], winner: Dict[str, Any]):
    """Async logging of auction results (for analytics)."""
    redis = await get_redis()
    await redis.lpush(
        "auction_logs",
        f"{winner['dsp_id']}|{winner['bid_amount']}"
    )
