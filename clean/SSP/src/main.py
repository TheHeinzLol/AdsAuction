#TODO remove .. in dependencies and models imports for container run
import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from time import perf_counter
from urllib.parse import urljoin
from uuid import uuid4

import aiohttp
from fastapi import FastAPI, Request, Response, status
from pydantic import ValidationError

from dependencies.database import async_engine
from models.models import Base
from shared.metrics_server import start_metrics_server
from shared.pydantic_models import (
    AdRenderOWS,
    AdRequestOWS,
    AdRequestSSP,
    AdResponseSSP,
    BidSSP,
    ModelAuctionsSSP,
    ModelBidsSSP,
)

from dependencies.redis import close_redis, get_redis
from .metrics import AD_REQUEST_DURATION, AD_REQUESTS_SENT
from .worker_insert import worker_insert
from .worker_render import worker_render

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s [%(funcName)s]:\n%(message)s",
    force=True
)
logging.getLogger("SSP.src.worker_insert").setLevel(logging.ERROR)
logging.getLogger("SSP.src.worker_render").setLevel(logging.DEBUG)

METRICS_PORT = int(os.getenv("METRICS_PORT", "8041"))
ADX_HOST = os.getenv("ADX_HOST", "localhost")
ADX_PORT = 8002 if ADX_HOST == "localhost" else 8000
ADX_URL = f"http://{ADX_HOST}:{ADX_PORT}"
CONCURRENCY = 150
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Get redis instance
    try:
        app.state.redis = await get_redis()
        logger.info("Redis initialized")
    except Exception as e:
        logger.error(f"Failed to get redis:\n{e}")
    # Create tables in postgres. Won't recreate if tables are already there.
    try:
        await create_database_tables()
        logger.info("Success: database tables created")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
    # Get api keys
    try:
        app.state.api_keys = await fetch_api_keys()
        logger.info(f"API keys:\n{json.dumps(app.state.api_keys, indent=2)}")
    except Exception as e:
        logger.error(f"Failed to fetch API keys:\n{e}")
    
    app.state.semaphore = asyncio.Semaphore(CONCURRENCY)
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.disabled = True
    prometheus_server, _thread = start_metrics_server(METRICS_PORT)
    connector = aiohttp.TCPConnector(enable_cleanup_closed=True)
    app.state.ad_request_session = aiohttp.ClientSession(connector=connector)

    workers = [
        asyncio.create_task(worker_insert(app.state.redis), name="insert"),
        asyncio.create_task(worker_render(app.state.redis), name="render")
        ]
    yield
    # stop workers
    for worker in workers: 
        worker.cancel()
        logger.info(f"Cancelling {worker.get_name()} worker")
    # close connections
    await app.state.ad_request_session.close()

    await close_redis()
    
    try:
        prometheus_server.shutdown()
        prometheus_server.server_close()
        _thread.join(timeout=2)
        logger.info("Prometheus metrics server shutdown success.")
    except Exception as e:
        logger.error(f"Failed to shutdown Prometheus metrics server:\n{e!s}")



app = FastAPI(lifespan=lifespan)

@app.post("/ad_request")
async def ssp_answer(payload: AdRequestOWS, request: Request) -> AdResponseSSP:
    # get redis
    redis = app.state.redis
    # get session
    session = request.app.state.ad_request_session
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
    adx_urls = [urljoin(ADX_URL, f"/ad_request_adx_{adx_id}") for adx_id in range(1)]
    # gather ads. These are pydantic models waiting to be unpacked
    time_created = datetime.now(UTC).timestamp()
    async def controlled_request(adx_url):
        async with semaphore:
            return await send_ad_request(
                session=session,
                url=adx_url,
                json=request_data,
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
                "auction_id_ssp": "auction_id",
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
        logger.debug(f"bids before rpush:\n{bids}")
        async with redis.pipeline() as pipe:
            for bid in bids:
                pipe.rpush(f"auction:{auction_id}:bids", json.dumps(bid))
                logging
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


@app.post("/confirm_render")
async def confirm_render(payload: AdRenderOWS, request: Request) -> dict:
    redis = request.app.state.redis
    try:
        await redis.rpush(f"auction:to_render", payload.auction_id_ssp)
    except Exception as e:
        logger.error(f"Failed to push render:\n{e}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/healthz")
async def healthz():
    return {"status": "healthy"}


@app.get("/refresh_keys")
async def refresh_keys(request: Request):
    request.app.state.api_keys = await fetch_api_keys()
    return app.state.api_keys


# ===== HELPERS =====
async def send_ad_request(
    session: aiohttp.ClientSession,
    url: str,
    json: dict,
    api_key: str,
) -> BidSSP:
    start = perf_counter()
    if api_key == "NO KEY":
        logger.warning(f"Cancelling ad request for {url}: No API key")
        return

    logger.debug(f"Sending request to {url}")
    before_request = perf_counter()
    time_sent = datetime.now(UTC).timestamp()
    async with session.post(url=url, headers={"X-API-KEY": api_key}, json=json) as response:
        response_time = perf_counter() - before_request
        time_received = datetime.now(UTC).timestamp()
        if response.status in [200, 204]:
            AD_REQUESTS_SENT.labels(status="success").inc()
            AD_REQUEST_DURATION.labels(status="success").observe(response_time)

            if response.status == 204:
                return response

            response_json = await response.json()
            response_json.update({
                "time_sent": time_sent,
                "time_received": time_received,
                "is_winning": False
            })
            logger.debug(f"Response:\n{response_json}")
            try:
                return BidSSP(**response_json)
            except ValidationError as e:
                logger.error(str(e))
        else:
            response_text = await response.text()
            logger.info(
                f"Ad request did not return 200. Got status: {response.status}\n"
                f"Response body:\n{response_text}"
            )
            AD_REQUESTS_SENT.labels(status="error").inc()
            AD_REQUEST_DURATION.labels(status="error").observe(response_time)
            return response


def determine_winner(bids: list[dict]) -> dict:
    winner = max(bids, key=lambda b: b["bid_amount"])
    return winner


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


def get_api_key(request: Request, adx_url: str):
    api_keys = request.app.state.api_keys
    adx_id = adx_url[-1]
    for key, key_data in api_keys.items():
        if key_data["adx_id"] == adx_id:
            return key
    logger.warning(f"Found no API key for {adx_id}")
    return "NO KEY"


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


# Helper functions
async def create_database_tables():
    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

