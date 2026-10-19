import asyncio
import logging
import os
from contextlib import asynccontextmanager
from urllib.parse import urljoin
from uuid import uuid4

import aiohttp
from fastapi import FastAPI, Request, Response, status
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s [%(funcName)s]:\n%(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # access_logger = logging.getLogger("uvicorn.access")
    # access_logger.disabled = True
    app.state.ad_request_session = aiohttp.ClientSession()
    # app.state.render_session = aiohttp.ClientSession()

    yield


app = FastAPI(lifespan=lifespan)
ADX_URL = os.getenv("ADX_URL", "http://localhost:8001")


class AdRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str
    publisher_id: str
    floor_price: float
    device: str
    channel: str
    ad_size: list | None
    region: str
    languages: list[str]
    local_hour: int
    category: str


class AdResponse(BaseModel):
    auction_id_ssp: str
    ad_url: str
    ttl: int


class UserInfo(BaseModel):
    user_id: str
    auction_id_ssp: str
    floor_price: float
    device: str
    channel: str
    ad_size: list | None
    region: str
    languages: list[str]
    local_hour: int
    category: str


@app.post("/ad_request")
async def ssp_answer(payload: AdRequest, request: Request) -> AdResponse:
    session = request.app.state.ad_request_session
    payload_dict = payload.model_dump()
    logger.debug(f"Raw payload dict:\n{payload_dict}")
    auction_id = str(uuid4())[:8]
    db_insert = {
        "auction_id_ssp": auction_id,
        "publisher_id": payload_dict.pop("publisher_id"),
    }
    json_user_info = {**payload_dict, "auction_id_ssp": auction_id}
    logger.debug(f"json_user_info:\n{json_user_info}")

    adx_urls = [urljoin(ADX_URL, f"/adx_{adx_id}_ad_request") for adx_id in range(3)]
    tasks = [
        send_ad_request(session=session, url=adx_url, json=json_user_info)
        for adx_url in adx_urls
    ]
    responses = await asyncio.gather(*tasks)
    bids = [response for response in responses if response is not None]
    if not bids:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    logger.debug(f"bids:\n{bids}")
    # This is overkill for a single line but I brought it out in case of complex
    # winner determination algo
    winner = determine_winner(bids)
    logger.debug(f"Winner:\n{winner}")
    ad_response = {**winner, "aucion_id_ssp": auction_id}
    db_insert["auction_id_adx"] = ad_response.pop("auction_id_adx")
    db_insert["win_adx_id"] = ad_response.pop("adx_id")
    db_insert["win_bid"] = ad_response.pop("bid_amount")

    logger.debug(f"ad_response:\n{ad_response}")
    logger.debug(f"db_insert:\n{db_insert}")

    return ad_response


@app.post("/confirm_render")
async def confirm_render() -> dict:

    return {"render": "accepted"}


@app.get("/healthz")
async def healthz():
    return {"status": "healthy"}


# ===== HELPERS =====
async def send_ad_request(session: aiohttp.ClientSession, url: str, json: dict) -> dict:
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
            if "bid_amount" in response_json:
                return response_json


def determine_winner(bids: list[dict]) -> dict:
    winner = max(bids, key=lambda b: b["bid_amount"])
    return winner
