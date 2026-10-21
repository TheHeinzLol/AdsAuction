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
    AuctionSSP # will be replaced with sqlalchemy schema
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s [%(funcName)s]:\n%(message)s",
)

ADX_URL = os.getenv("ADX_URL", "http://localhost:8001")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # access_logger = logging.getLogger("uvicorn.access")
    # access_logger.disabled = True
    app.state.ad_request_session = aiohttp.ClientSession()
    # app.state.render_session = aiohttp.ClientSession()

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

    try:
        AdRequestSSP.model_validate(request_data)
    except ValidationError as e:
        logger.error(str(e))
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    logger.debug(f"request_data:\n{request_data}")
    # a crutch for adx endpoints 
    # TODO make it pretty
    adx_urls = [urljoin(ADX_URL, f"/adx_{adx_id}_ad_request") for adx_id in range(3)]
    # gather ads. These are pydantic models waiting to be unpacked
    tasks = [
        send_ad_request(session=session, url=adx_url, json=request_data)
        for adx_url in adx_urls
    ]
    responses = await asyncio.gather(*tasks)
    # collect bids. These are pydantic models unpacked into list of dicts
    bids = [response.model_dump() for response in responses if response is not None]
    if not bids:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    logger.debug(f"bids:\n{bids}")
    # This is overkill for a single line but I brought it out in case of complex
    # winner determination algo
    winner = determine_winner(bids)
    ad_response= {
            **{key: winner[key] for key in winner.keys() if key in list(AdResponseSSP.model_fields)},
            "auction_id_ssp": auction_id
    }
    db_insert= {
            **{key: winner[key] for key in winner.keys() if key in list(AuctionSSP.model_fields)},
            "auction_id_ssp": auction_id
    }
    logger.debug(f"Winner:\n{winner}")
    logger.debug(f"ad_response:\n{ad_response}")
    logger.debug(f"db_insert:\n{db_insert}")
    try:
        AdResponseSSP.model_validate(ad_response)
        return AdResponseSSP(**ad_response)
    except ValidationError as e:
        logger.error(str(e))


@app.post("/confirm_render")
async def confirm_render() -> dict:

    return {"render": "accepted"}


@app.get("/healthz")
async def healthz():
    return {"status": "healthy"}


# ===== HELPERS =====
async def send_ad_request(session: aiohttp.ClientSession, url: str, json: dict) -> AdResponseADX:
    logger.debug(f"Sending request to {url}")
    async with session.post(url=url, json=json) as response:
        if response.status != 200:
            response_text = await response.text()
            logger.info(
                f"Ad request did not return 200. Got status: {response.status}\n"
                f"Response body:\n{response_text}"
            )
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


