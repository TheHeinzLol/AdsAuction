import logging
import os
from contextlib import asynccontextmanager
from random import choice  # for choosing a ttl
from urllib.parse import urljoin
from uuid import uuid4

import aiohttp
from fastapi import FastAPI, Response, status
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

class AdResponse(BaseModel):
    adx_id: str
    auction_id_ssp: str
    ad_url: str
    bid_amount: float
    ttl: int



@app.post("/ad_request")
async def ssp_answer(payload: AdRequest) -> dict:
    payload_dict = payload.model_dump()
    logger.debug(f"Raw payload dict:\n{payload_dict}")
    publisher_id = payload_dict.pop("publisher_id")
    auction_id = str(uuid4())[:8]
    json_adx = {**payload_dict, **{"auction_id_ssp": auction_id}}
    logger.debug(f"json_adx:\n{json_adx}")
    async with aiohttp.ClientSession() as session:
        bids = []
        for adx_id in range(3):
            logger.debug(f"Sending request to adx_{adx_id}")
            # TODO bring out adx ad request to separate funcion
            # TODO handle empty bids
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
                    logger.debug(f"response:\n{resp}")
                    if "bid_amount" in resp:
                        bids.append(resp)
        if not bids:
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        winner = max(bids, key=lambda b:b["bid_amount"])
        logger.debug(f"Winner:\n{winner}")
        ad_response = {**winner, **{"aucion_id_ssp": auction_id}}
        del ad_response["auction_id"]
        logger.debug(f"ad_response:\n{ad_response}")

        return ad_response


@app.post("/confirm_render")
async def confirm_render() -> dict:

    return {"render": "accepted"}


@app.get("/healthz")
async def healthz():
    return {"status": "healthy"}
