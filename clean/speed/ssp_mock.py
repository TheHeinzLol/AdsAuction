import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from urllib.parse import urljoin
from uuid import uuid4

import aiohttp
from fastapi import FastAPI, Request, Response, status
from pydantic import BaseModel, ConfigDict

#=====CONST=====
ADX_URL = "http://localhost:8002/"
#adx_urls = [urljoin(ADX_URL, "/test") for adx_id in range(1)]
adx_urls = [urljoin(ADX_URL, f"ad_request_adx_{adx_id}") for adx_id in range(3)]
ad_request_ssp = {
    "user_id": "user_12345",
    "category": "technology",
    "floor_price": 0.50,
    "device": "mobile",
    "channel": "web",
    "ad_size": [300, 250],
    "region": "DE",
    "languages": ["de", "en"],
    "local_hour": 14,
    "auction_id_ssp": "ssp_auction_98765"
}
ad_response_ssp = {
    "auction_id_ssp": "ssp_auction_98765",
    "creative_url": "https://cdn.example.com/ads/creative_001.html",
    "ttl": 300,
    "render_beacon": "https://tracking.example.com/render/ssp_auction_98765"
}
concurrency = 150
class AdRequestCommon(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str
    category: str
    floor_price: float  # temp until publisher policy is implemented
    device: str
    channel: str
    ad_size: tuple[int, int] | None
    region: str
    languages: list[str]
    local_hour: int

class AdRequestOWS(AdRequestCommon):
    publisher_id: str

class AdRequestSSP(AdRequestCommon):
    auction_id_ssp: str


class AdResponseSSP(BaseModel):
    model_config = ConfigDict(extra="forbid")

    auction_id_ssp: str
    creative_url: str
    ttl: int
    render_beacon: str

class AdResponseADX(AdResponseSSP):
    adx_id: str
    auction_id_adx: str
    creative_url: str
    bid_amount: float
    categories: list[str]

class BidSSP(AdResponseADX):

    time_sent: float
    time_received: float
    is_winning: bool

class ModelAuctionsSSP(BaseModel):
    auction_id: str
    time_created: float
    time_closed: float
    publisher_id: str
    winner: str | None
    winner_bid: float | None
    is_rendered: bool
#====/CONST=====

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s [%(funcName)s]:\n%(message)s",
    force=True
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.api_keys = await fetch_api_keys()
    app.state.semaphore = asyncio.Semaphore(concurrency)
    app.state.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(enable_cleanup_closed=True))
    yield
    await app.state.session.close()

app = FastAPI(lifespan=lifespan)

@app.post("/test")
async def asstwat():
    return ad_response_ssp

#@app.post("/ad_request")
async def faf(payload: dict, request: Request):
    session = request.app.state.session

    semaphore = request.app.state.semaphore
    async def controlled_request(url):
        async with semaphore:
            return await send_ad_request(session, url, ad_request_ssp, get_api_key(request, url))

    tasks = [controlled_request(url) for url in adx_urls]
    results = await asyncio.gather(*tasks)
    return ad_response_ssp

async def send_ad_request(session, url, payload, api_key):
    time_sent = datetime.now(UTC).timestamp()
    async with session.post(url=url, headers={"X-API-KEY": api_key}, json=payload) as response:
        time_received = datetime.now(UTC).timestamp()
        response_json = await response.json()
        response_json.update({
            "time_sent": time_sent,
            "time_received": time_received,
            "is_winning": False
        })
        return BidSSP(**response_json)

def get_api_key(request: Request, adx_url: str):
    api_keys = request.app.state.api_keys
    adx_id = adx_url[-1]
    for key, key_data in api_keys.items():
        if key_data["adx_id"] == adx_id:
            return key
    return "test_key"

async def fetch_api_keys():
    async with aiohttp.ClientSession() as session:  # noqa: SIM117
        async with session.get(url=urljoin(ADX_URL, "/fetch_api_keys")) as response:
            if response.status != 200:
                response_text = await response.text()
                logger.info(
                    f"Fetching keys did not return 200. Got status: {response.status}\n"
                    f"Response body:\n{response_text}"
                )
            else:
                response_json = await response.json()
                logger.debug(f"Got keys:\n{response_json}")
                return response_json


@app.post("/ad_request")
async def ssp_answer(payload: AdRequestOWS, request: Request) -> AdResponseSSP:
    # get redis
    redis = None#app.state.redis
    # get session
    session = request.app.state.session
    semaphore = request.app.state.semaphore
    # cast pydantic model into dict
    request_data = payload.model_dump()
    logger.debug(f"Raw payload dict:\n{request_data}")
    # generate auction id
    auction_id = str(uuid4())
    request_data["auction_id_ssp"] = auction_id
    publisher_id = request_data.pop("publisher_id")
    logger.debug(f"request_data:\n{request_data}")
    # a crutch for adx endpoints
    adx_urls = [urljoin(ADX_URL, f"/ad_request_adx_{adx_id}") for adx_id in range(3)]
    # gather ads. These are pydantic models waiting to be unpacked
    time_created = datetime.now(UTC).timestamp()
    async def controlled_request(adx_url):
        async with semaphore:
            return await send_ad_request(
                session=session,
                url=adx_url,
                payload=request_data,
                api_key=get_api_key(request=request, adx_url=adx_url)
            )
    tasks = [controlled_request(adx_url) for adx_url in adx_urls ]
    responses = await asyncio.gather(*tasks)
    bids, need_update_keys = process_responses(responses)
    logger.debug(f"bids:\n{bids}")

    if not bids:
        db_insert = {
                "auction_id": auction_id,
                "winner": None,
                "winner_bid": None,
                "time_closed": datetime.now(UTC).timestamp(),
                }
    else:
        # This is overkill for a single line but I brought it out in case of complex
        winner = determine_winner(bids)
        time_closed = datetime.now(UTC).timestamp()
        winner["is_winning"] = True
        db_insert = {**winner, "time_closed": time_closed}
        logger.debug(f"Winner:\n{winner}")
        # == func prepare db insert===
        data_model_map = {
                "auction_id_ssp":"auction_id",
                "adx_id": "winner",
                "bid_amount": "winner_bid"
        }

        for old_key, new_key in data_model_map.items():
            db_insert[new_key] = db_insert.pop(old_key)
        # == func prepare db insert=== end

    db_insert.update({"publisher_id": publisher_id, "time_created": time_created, "is_rendered": False})
    db_insert = ModelAuctionsSSP.model_validate(db_insert, extra="ignore").model_dump()
    logger.debug(f"db_insert:\n{db_insert}")


    # find a good place for this if
    if need_update_keys:
        request.app.state.api_keys = await fetch_api_keys()
    if redis:
        async with redis.pipeline() as pipe:
            for bid in bids:
                pipe.rpush(f"auction:{auction_id}:bids", json.dumps(bid))
            pipe.rpush(f"auction:{auction_id}", json.dumps(db_insert))
            pipe.rpush("auction:to_process", auction_id)
            await pipe.execute()
        # no bids handling
    if not bids:
        # TODO insert empty auction in db
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    ad_response = AdResponseSSP.model_validate(winner, extra="ignore")
    logger.debug(f"ad_response:\n{ad_response}")
    return ad_response

def determine_winner(bids: list[dict]) -> dict:
    winner = max(bids, key=lambda b: b["bid_amount"])
    return winner

def process_responses(
    responses: list[aiohttp.ClientResponse | BidSSP],
) -> tuple[list[dict], bool]:

    bids = []
    need_key_update = False

    for response in responses:
        if isinstance(response, aiohttp.ClientResponse):
            need_key_update = True
            continue
        elif response is not None:
            bids.append(response.model_dump())
        else:
            continue
    return bids, need_key_update

