import logging
from contextlib import asynccontextmanager
from random import choice, random, uniform
from uuid import uuid4

from fastapi import Body, FastAPI, Request, Response, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s [%(funcName)s]:\n%(message)s",
)

num_adx_endpoints = 3


class AdResponse(BaseModel):
    """
    This dict is returned to ssp as answer for ad request.
    """

    adx_id: str
    auction_id_adx: str
    auction_id_ssp: str
    ad_url: str
    bid_amount: float
    ttl: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        for adx_id in range(num_adx_endpoints):
            app.add_api_route(
                path=f"/adx_{adx_id}_ad_request",
                endpoint=adx_ad_request,
                response_model=AdResponse,
                methods=["POST"],
            )
            app.add_api_route(
                path=f"/adx_{adx_id}_render_confirm",
                endpoint=adx_render_confirm,
                methods=["POST"],
            )
    except Exception as e:
        logger.error(f"Failed to create endpoints:\n{e}")
    else:
        logger.info(f"Created {num_adx_endpoints} endpoints")
    yield


app = FastAPI(title="ADX mock", lifespan=lifespan)


@app.get("/")
async def get_root():
    return {"ass": "twat"}


@app.get("/healthz")
async def helth_check():
    return {"status": "healthy"}


# ===== Helper functions =====


async def adx_ad_request(request: Request, payload: dict = Body):
    adx_id = request.url.path.split("/")[-1]
    auction_id_ssp = payload["auction_id_ssp"]
    logger.debug(f"auction_id_ssp:\n{auction_id_ssp}")
    if random() < 0.99:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return {
        "adx_id": adx_id,
        "auction_id_adx": str(uuid4())[:8],
        "auction_id_ssp": auction_id_ssp,
        "ad_url": f"{adx_id} mock ad url",
        "bid_amount": round(uniform(0, 6), 2),
        "ttl": choice([5, 10, 15]),
    }


async def adx_render_confirm(request: Request):
    adx_id = request.url.path.split("/")[-1]

    return {"adx_id": adx_id, "render_status": "confirmed"}
