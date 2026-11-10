import asyncio
import logging
import os
from contextlib import asynccontextmanager
from time import perf_counter
from urllib.parse import urljoin
from uuid import uuid4

import aiohttp
from datetime import datetime, UTC
from fastapi import FastAPI, Request, Response, status
from pydantic import ValidationError

from dependencies.redis import close_redis, get_redis
from shared.metrics_server import start_metrics_server
from shared.pydantic_models import (
    AdRequestOWS,
    AdRequestSSP,
    AdResponseADX,
    AdResponseSSP,
)

from .metrics import AD_REQUEST_DURATION, AD_REQUESTS_SENT

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s [%(funcName)s]:\n%(message)s",
)

METRICS_PORT = int(os.getenv("METRICS_PORT", "8041"))
ADX_HOST = os.getenv("ADX_HOST", "localhost")
ADX_PORT = os.getenv("ADX_PORT", "8002")
ADX_URL = f"http://{ADX_HOST}:{ADX_PORT}"

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        app.state.redis = await get_redis()
    except Exception as e:
        logger.error(f"Failed to get redis:\n{e}")

    await create_database_tables()
    # access_logger = logging.getLogger("uvicorn.access")
    prometheus_server, _thread = start_metrics_server(METRICS_PORT)
    # access_logger.disabled = True
    app.state.ad_request_session = aiohttp.ClientSession()
    app.state.render_session = aiohttp.ClientSession()
    # Get api keys
    try:
        app.state.api_keys = await fetch_api_keys()
    except Exception as e:
        logger.error(f"Failed to fetch API keys:\n{e}")
    yield
    
    await app.state.ad_request_session.close()
    await app.state.render_session.close()
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
    # get session
    session = request.app.state.ad_request_session
    # cast pydantic model into dict
    request_data = payload.model_dump()
    logger.debug(f"Raw payload dict:\n{request_data}")
    # generate auction id
    auction_id = str(uuid4())
    # db_insert is a placeholder for later insert.
    # With next two lines we swap publisher_id in request_data  with current auction id
    # while saving publisher id for later insert.
    publisher_id = request_data.pop("publisher_id")}
    request_data["auction_id_ssp"] = auction_id
    logger.debug(f"request_data:\n{request_data}")
    # a crutch for adx endpoints
    # TODO make it pretty
    adx_urls = [urljoin(ADX_URL, f"/adx_{adx_id}_ad_request") for adx_id in range(3)]
    # gather ads. These are pydantic models waiting to be unpacked
    time_opened = datetime.now(UTC)
    tasks = [
        send_ad_request(
            session=session,
            url=adx_url,
            json=AdRequestSSP(**request_data),
            api_key=get_api_key(request=request, adx_url=adx_url),
        )
        for adx_url in adx_urls
    ]
    responses = await asyncio.gather(*tasks)
    bids, need_update_keys = process_responses(responses)
    logger.debug(f"bids:\n{bids}")
    if need_update_keys:
        request.app.state.api_keys = await fetch_api_keys()
    # no bids handling
    if not bids:
        # TODO insert empty auction in db
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    # This is overkill for a single line but I brought it out in case of complex
    winner = determine_winner(bids)
    time_closed = datetime.now(UTC)
    logger.debug(f"Winner:\n{winner}")
    data_model_map = {
            "auction_id_ssp":"auction_id",
            "adx_id": "winner",
            "bid_amount": "winner_bid"
    }
    db_insert = {**winner, "publisher_id": publisher_id}
    db_insert["is_rendered"] = False
    db_insert.update({"time_created": time_created, "time_closed": time_closed})
    for old_key, new_key in data_model_map.items():
        db_insert[new_key] = db_insert.pop(old_key)
    logger.debug(f"db_insert:\n{db_insert}")
    # TODO insert db_insertt into redis queue
    ad_response = AdResponseSSP.model_validate(winner, extra="ignore")
    logger.debug(f"ad_response:\n{ad_response}")

    return ad_response


@app.post("/confirm_render")
async def confirm_render(payload: dict, request: Request) -> dict:
    # session = request.app.state.ad_request_session
    # search auction ID in redis or db
    # pass render into corresponding adx
    return Response(status_code=status.HTTP_204_NO_CONTENT)


from ..dependencies.database import DBSession
@app.post("/insert")
async def test_insert(db: DBSession) -> None:
    from sqlalchemy import insert
    from sqlalchemy.exc import IntegrityError

    # foolows after db_insert = {**winner, "publisher_id": publisher_id}
    data = {
        "auction_id_ssp": str(uuid4()),
        "ad_url": "adx_2 mock ad url",
        "ttl": 5,
        "adx_id": "adx_2",
        "auction_id_adx": str(uuid4()),
        "bid_amount": 5.59,
        "categories": ["gaming", "movies"],
        "publisher_id": "pub_espn",
    }
    data_model_map = {
            "auction_id_ssp":"auction_id",
            "adx_id": "winner",
            "bid_amount": "winner_bid"
    }
    db_insert["is_rendered"] = False
    db_insert.update({"time_created": time_created, "time_closed": time_closed})
    # single
    for old_key, new_key in data_model_map.items():
        db_insert[new_key] = db_insert.pop(old_key)
    # bulk
    bulk_data = [{**db_insert, "auction_id": str(uuid4())} for _ in range(3)]
    try:
        await db.execute(insert(Auction.__table__), db_insert)
    except IntegrityError as e:
        logger.error(f"Failed the insert:\n{e}")
        return {"insert failed": e}
    try:
        await db.execute(insert(Auction.__table__), bulk_data)
    except IntegrityError as e:
        logger.error(f"Failed the bulk insert:\n{e}")
        return {"bulk insert failed": e}
    try:
        await db.commit()
    except IntegrityError  as e:
        logger.error(f"Failed the commit:\n{e}")
        return {"commit failed": e}
    stmt = insert().values
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
    json: AdRequestSSP,
    api_key: str,
) -> AdResponseADX:

    if api_key == "NO KEY":
        logger.warning(f"Cancelling ad request for {url}: No API key")
        return

    logger.debug(f"Sending request to {url}")
    before_request = perf_counter()
    async with session.post(
        url=url, headers={"X-API-KEY": api_key}, json=json.model_dump()
    ) as response:
        response_time = perf_counter() - before_request
        if response.status != 200:
            response_text = await response.text()
            logger.info(
                f"Ad request did not return 200. Got status: {response.status}\n"
                f"Response body:\n{response_text}"
            )
            AD_REQUESTS_SENT.labels(status="error").inc()
            AD_REQUEST_DURATION.labels(status="error").observe(response_time)
            if response.status in [401, 403]:
                return response
        else:
            response_json = await response.json()
            logger.debug(f"Response:\n{response_json}")
            AD_REQUESTS_SENT.labels(status="success").inc()
            AD_REQUEST_DURATION.labels(status="success").observe(response_time)
            try:
                AdResponseADX.model_validate(response_json)
                return AdResponseADX(**response_json)
            except ValidationError as e:
                logger.error(str(e))


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
    adx_id = adx_url.split("/")[-1].split("_")[1]
    for key, key_data in api_keys.items():
        if key_data["adx_id"] == adx_id:
            return key
    logger.warning(f"Found no API key for {adx_id}")
    return "NO KEY"


def process_responses(
    responses: list[aiohttp.ClientResponse | AdResponseADX],
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
    from dependencies.database import async_engine
    from models.models import Base

    try:
        async with async_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        print("Success: database tables created")
    except Exception as e:
        print(f"Failed to create tables: {e}")
