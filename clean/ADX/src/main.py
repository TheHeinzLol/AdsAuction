
import logging
import os
import secrets
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from random import choice, choices, randint, random, uniform
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, Request, Response, status
from pydantic import ValidationError

from shared.pydantic_models import AdRequestSSP, AdResponseADX

from pathlib import Path 
import fcntl
import json

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.FATAL,
    format="%(levelname)s [%(funcName)s]:\n%(message)s",
)

num_adx_endpoints = int(os.getenv("NUMBER_OF_ADX", "3"))
valid_api_keys = {}
test_api_key = os.getenv("TEST_API_KEY", "test_api_key")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.stamps = [0,0,0]
    # create adx endpoints
    try:
        for adx_id in range(num_adx_endpoints):
            app.add_api_route(
                path=f"/ad_request_adx_{adx_id}",
                endpoint=adx_ad_request,
                response_model=AdResponseADX,
                methods=["POST"],
            )
            app.add_api_route(
                path=f"/render_confirm_adx_{adx_id}",
                endpoint=adx_render_confirm,
                methods=["POST"],
            )
    except Exception as e:
        logger.error(f"Failed to create endpoints:\n{e}")
    else:
        logger.info(f"Created {num_adx_endpoints} endpoints")
    #turn off endpoints info
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.disabled = True
    # make API keys
    global valid_api_keys
    valid_api_keys = load_or_generate_keys(num_adx_endpoints)
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


@app.get("/update_keys")
async def update_keys():
    valid_api_keys.clear()
    for i in range(num_adx_endpoints):
        valid_api_keys[secrets.token_urlsafe(16)] = {
            "adx_id": str(i),
            "created_at": datetime.now(UTC).isoformat(),
        }
    return valid_api_keys

@app.post("/test")
async def test_speed(payload: dict):
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/stamps")
async def get_stamps(request: Request):
    result = [s/2500 for s in request.app.state.stamps]
    request.app.state.stamps = [0,0,0]
    return {"stamps": result}
# ===== Helper functions =====
from time import perf_counter
async def adx_ad_request(
    request: Request, payload: AdRequestSSP, x_api_key: str = Header()
):
    if random() < 0.1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    stamps = request.app.state.stamps
    start = perf_counter()
    adx_id = request.url.path[-1]

    if x_api_key != test_api_key:
        if x_api_key not in valid_api_keys:
            raise HTTPException(status_code=401, detail="Invalid API key")

        if valid_api_keys[x_api_key]["adx_id"] != adx_id:
            raise HTTPException(
                status_code=403, detail="API key doesn't match this adx"
            )
    stamps[0] += perf_counter() - start
    start = perf_counter()
    payload = payload.model_dump()
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
    stamps[1] += perf_counter() - start
    start = perf_counter()
    logger.debug(f"auction_id_ssp:\n{auction_id_ssp}")
    ad_response = {
        "adx_id": adx_id,
        "auction_id_ssp": auction_id_ssp,
        "bid_amount": round(uniform(0, 6), 2),
        "creative_url": f"{adx_id} mock ad url",
        "categories": categories,
        "ttl": choice([5, 10, 15]),
        "render_beacon": f"beacon_{adx_id}"
    }
    try:
        AdResponseADX.model_validate(ad_response)
        stamps[2] += perf_counter() - start
        return AdResponseADX(**ad_response)
    except ValidationError as e:
        logger.error(str(e))


async def adx_render_confirm():
    return Response(status_code=status.HTTP_204_NO_CONTENT)

KEY_FILE = Path.cwd()/"adx_api_keys.json"
def load_or_generate_keys(num_endpoints: int) -> dict:
    lock_file = KEY_FILE.with_suffix(".lock")
    keys = {} 
    with open(lock_file, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)  # Exclusive lock
        try:
            if KEY_FILE.exists():
                with open(KEY_FILE) as f:
                    return json.load(f)
            
            for i in range(num_endpoints):
                keys[secrets.token_urlsafe(16)] = {
                    "adx_id": str(i),
                    "created_at": datetime.now(UTC).isoformat(),
                }
                
            tmp = KEY_FILE.with_suffix(".tmp")
            with open(tmp, "w") as f:
                json.dump(keys, f)
            tmp.rename(KEY_FILE)
            return keys
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
