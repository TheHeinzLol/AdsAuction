import logging
import os
from contextlib import asynccontextmanager
from random import choice  # for choosing a ttl
from urllib.parse import urljoin
from uuid import uuid4

import aiohttp
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.disabled = True

    yield


app = FastAPI()#(lifespan=lifespan)
ADX_URL = os.getenv("ADX_URL", "http://localhost:8001")


class AdRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str
    publisher_id: str
    device: str
    channel: str
    ad_size: list | None
    region: str
    languages: list[str]
    local_hour: int
    category: str
    floor_price: float


@app.post("/ad_request")
async def ssp_answer(payload: AdRequest) -> dict:
    payload_dict = payload.model_dump()
    publisher_id = payload_dict.pop("publisher_id")
    auction_id = str(uuid4())[:8]
    json_adx = {**payload_dict, **{"auction_id_ssp": auction_id}}
    logger.debug(f"\nPayload:\n{payload_dict}\njson_adx:\n{json_adx}")
    async with aiohttp.ClientSession() as session:
        bids = []
        for adx_id in range(3):
            logger.debug(f"Sending request to adx_{adx_id}")
            # TODO bring out adx ad request to separate funcion
            async with session.post(
                url=urljoin(ADX_URL, f"/adx_{adx_id}_ad_request"),
                json=json_adx
            ) as response:
                resp = await response.json()
                if response.status != 200:
                    logger.info(
                        f"Ad request did not return 200. Got status: {response.status}\n"
                        f"Response body:\n{resp}"
                    )
                else:
                    logger.debug(f"\nresponse:\n{resp}")
                    bids.append(resp)

        winner = max(bids, key=lambda b:b["bid_amount"])
        ad_response = {**winner, **{"aucion_id_ssp": auction_id}}
        logger.debug(f"\nad_response:\n{ad_response}")
        logger.debug(f"\nWinner:\n{winner}")
        del ad_response["auction_id"]
        return ad_response


@app.post("/confirm_render")
async def confirm_render() -> dict:

    return {"render": "accepted"}


@app.get("/healthz")
async def healthz():
    return {"status": "healthy"}
