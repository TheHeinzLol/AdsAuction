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
logger.basicConfig(level=logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.disabled = True

    yield


app = FastAPI(lifespan=lifespan)
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

    async with aiohttp.ClientSession as session:
        for adx_id in range(3):
            async with session.post(
                url=urljoin(ADX_URL, f"/adx_{adx_id}_ad_request"), json=payload
            ) as response:
                resp = response.json()
                if response.status != 200:
                    logger.info(
                        f"Ad request did not return 200. Got status: {response.status}\n"
                        f"Response body:\n{resp}"
                    )
                else:
                    return {
                        "ad_url": "ssp to ows mock ad url",
                        "auction_id": str(uuid4())[:8],  # to escape dealing with long id for a simple mock
                        "ttl": choice([5, 10, 15]),
                    }


@app.post("/confirm_render")
async def confirm_render() -> dict:
    return {"render": "accepted"}


@app.get("/healthz")
async def healthz():
    return {"status": "healthy"}
