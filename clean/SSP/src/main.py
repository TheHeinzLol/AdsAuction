import asyncio
import logging
import os
from contextlib import asynccontextmanager
from urllib.parse import urljoin
from uuid import uuid4

import aiohttp
from fastapi import FastAPI, Request, Response, status
from pydantic import ValidationError

from shared.pydantic_models import (
    AdRequestOWS,
    AdRequestSSP,
    AdResponseADX,
    AdResponseSSP,
    AuctionSSP,  # will be replaced with sqlalchemy schema
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s [%(funcName)s]:\n%(message)s",
)

ADX_URL = os.getenv("ADX_URL", "http://localhost:8002")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # access_logger = logging.getLogger("uvicorn.access")
    # access_logger.disabled = True
    app.state.ad_request_session = aiohttp.ClientSession()
    # app.state.render_session = aiohttp.ClientSession()
    # Get api keys
    app.state.api_keys = await fetch_api_keys()

    yield


app = FastAPI(lifespan=lifespan)


@app.post("/ad_request")
async def ssp_answer(payload: AdRequestOWS, request: Request) -> AdResponseSSP:
    # get session
    session = request.app.state.ad_request_session
    # cast pydantic model into dict
    request_data = payload.model_dump()
    logger.debug(f"Raw payload dict:\n{request_data}")
    # generate auction id
    auction_id = str(uuid4())[:8]
    # db_insert is a placeholder for later insert.
    # With next two lines we swap publisher_id in request_data  with current auction id
    # while saving publisher id for later insert.
    db_insert = {"publisher_id": request_data.pop("publisher_id")}
    request_data["auction_id_ssp"] = auction_id
    logger.debug(f"request_data:\n{request_data}")
    # a crutch for adx endpoints
    # TODO make it pretty
    adx_urls = [urljoin(ADX_URL, f"/adx_{adx_id}_ad_request") for adx_id in range(3)]
    # gather ads. These are pydantic models waiting to be unpacked
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
    logger.debug(f"Winner:\n{winner}")
    ad_response = AdResponseSSP.model_validate(winner, extra="ignore")
    logger.debug(f"ad_response:\n{ad_response}")
    db_insert = AuctionSSP.model_validate(
        {**winner, "publisher_id": db_insert["publisher_id"]}, extra="ignore"
    )
    logger.debug(f"db_insert:\n{db_insert}")

    return ad_response


@app.post("/confirm_render")
async def confirm_render() -> dict:

    return {"render": "accepted"}


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
    async with session.post(
        url=url, headers={"X-API-KEY": api_key}, json=json.model_dump()
    ) as response:
        if response.status != 200:
            response_text = await response.text()
            logger.info(
                f"Ad request did not return 200. Got status: {response.status}\n"
                f"Response body:\n{response_text}"
            )
            if response.status in [401, 403]:
                return response
        else:
            response_json = await response.json()
            logger.debug(f"Response:\n{response_json}")
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
