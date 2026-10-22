import logging
import secrets
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from random import choice, choices, randint, random, uniform
from uuid import uuid4

from fastapi import Body, FastAPI, Header, HTTPException, Request, Response, status
from pydantic import ValidationError

from shared.pydantic_models import AdResponseADX

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s [%(funcName)s]:\n%(message)s",
)

num_adx_endpoints = 3
valid_api_keys = {}
spare_api_key = "spare_key69"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # create adx endpoints
    try:
        for adx_id in range(num_adx_endpoints):
            app.add_api_route(
                path=f"/adx_{adx_id}_ad_request",
                endpoint=adx_ad_request,
                response_model=AdResponseADX,
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
    # make API keys
    for i in range(num_adx_endpoints):
        valid_api_keys[secrets.token_urlsafe(16)] = {
            "adx_id": str(i),
            "created_at": datetime.now(UTC).isoformat(),
        }
    logger.info(f"Valid API keys:{'\n'.join([key for key in valid_api_keys])}")
    yield


app = FastAPI(title="ADX mock", lifespan=lifespan)


@app.get("/")
async def get_root():
    return {"ass": "twat"}


@app.get("/fetch_api_keys")
async def give_api_keys():
    return valid_api_keys


@app.get("/healthz")
async def helth_check():
    return {"status": "healthy"}


# ===== Helper functions =====


async def adx_ad_request(
    request: Request, payload: dict = Body, x_api_key: str = Header
):
    if random() < 0.1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    if x_api_key not in valid_api_keys:
        raise HTTPException(status_code=401, detail="Invalid API key")

    adx_id = "_".join(
        request.url.path.split("/")[-1].split("_")[:2]
    )  # returns 'adx_i' where i is id

    if valid_api_keys[x_api_key]["adx_id"] != adx_id[-1]:
        raise HTTPException(status_code=403, detail="API key doesn't match this adx")

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
    ad_response = {
        "adx_id": adx_id,
        "auction_id_adx": str(uuid4())[:8],
        "auction_id_ssp": auction_id_ssp,
        "bid_amount": round(uniform(0, 6), 2),
        "ad_url": f"{adx_id} mock ad url",
        "categories": categories,
        "ttl": choice([5, 10, 15]),
    }
    try:
        AdResponseADX.model_validate(ad_response)
        return AdResponseADX(**ad_response)
    except ValidationError as e:
        logger.error(str(e))


async def adx_render_confirm(request: Request):
    adx_id = request.url.path.split("/")[-1]

    return {"adx_id": adx_id, "render_status": "confirmed"}
