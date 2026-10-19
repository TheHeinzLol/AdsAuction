import logging
from contextlib import asynccontextmanager
from random import choice, choices, randint, random, uniform
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
    bid_amount: float
    ad_url: str
    categories: list[str]
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
    if random() < 0.1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    adx_id = request.url.path.split("/")[-1]
    auction_id_ssp = payload["auction_id_ssp"]
    categories_good = [
        "technology",
        "gaming",
        "sports",
        "finance",
        "fashion",
        "health",
        "food",
        "pets",
        "movies",
        "music",
        "travel",
    ]
    categories_bad = ["gambling", "porn", "anime", "AI"]
    categories = choices(categories_good, k=randint(1, 3))
    if random() < 0.1:
        categories.append(choice(categories_bad))
    logger.debug(f"auction_id_ssp:\n{auction_id_ssp}")

    return {
        "adx_id": adx_id,
        "auction_id_adx": str(uuid4())[:8],
        "auction_id_ssp": auction_id_ssp,
        "bid_amount": round(uniform(0, 6), 2),
        "ad_url": f"{adx_id} mock ad url",
        "categories": categories,
        "ttl": choice([5, 10, 15]),
    }


async def adx_render_confirm(request: Request):
    adx_id = request.url.path.split("/")[-1]

    return {"adx_id": adx_id, "render_status": "confirmed"}
