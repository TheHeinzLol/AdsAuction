import fcntl
import json
import logging
import secrets
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from random import choice, choices, randint, random, uniform
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.FATAL,
    format="%(levelname)s [%(funcName)s]:\n%(message)s",
)
num_adx_endpoints = 3
valid_api_keys = {}
test_api_key = "test_api_key"

class AdRequestCommon(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str
    category: str
    floor_price: float  # temp until publisher policy is implemented
    device: str
    channel: str
    ad_size: tuple[int, int] | None
    region: str
    languages: list[str]
    local_hour: int

class AdRequestSSP(AdRequestCommon):
    auction_id_ssp: str

class AdResponseSSP(BaseModel):
    model_config = ConfigDict(extra="forbid")

    auction_id_ssp: str
    creative_url: str
    ttl: int
    render_beacon: str

class AdResponseADX(AdResponseSSP):
    adx_id: str
    auction_id_adx: str
    creative_url: str
    bid_amount: float
    categories: list[str]

ad_response_adx = {
    "auction_id_ssp": "ssp_auction_98765",
    "creative_url": "https://cdn.example.com/ads/creative_001.html",
    "ttl": 300,
    "render_beacon": "https://tracking.example.com/render/ssp_auction_98765",
    "adx_id": "adx_001",
    "auction_id_adx": "adx_auction_12345",
    "bid_amount": 1.25,
    "categories": ["technology", "electronics"],
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # create adx endpoints
    try:
        for adx_id in range(num_adx_endpoints):
            app.add_api_route(
                path=f"/ad_request_adx_{adx_id}",
                endpoint=adx_ad_request,
                # response_model=AdResponseADX,
                methods=["POST"],
            )
    except Exception as e:
        logger.error(f"Failed to create endpoints:\n{e}")
        raise
    # make API keys
    global valid_api_keys
    valid_api_keys = load_or_generate_keys(num_adx_endpoints)
    logger.info(f"Valid API keys:{'\n'.join([key for key in valid_api_keys])}")
    yield

app = FastAPI(title="ADX mock", lifespan=lifespan)

@app.post("/test")
async def test_speed():
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/fetch_api_keys")
async def give_api_keys():
    return valid_api_keys

async def adx_ad_request_(request: Request, payload: AdRequestSSP, x_api_key: str = Header()):
   # if random() < 0.1:
   #     return Response(status_code=status.HTTP_204_NO_CONTENT)

    adx_id = request.url.path[-1]

    if x_api_key != test_api_key:
        if x_api_key not in valid_api_keys:
            raise HTTPException(status_code=401, detail="Invalid API key")
   
        if valid_api_keys[x_api_key]["adx_id"] != adx_id:
            raise HTTPException(
                status_code=403, detail="API key doesn't match this adx"
            )
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
    logger.debug(f"auction_id_ssp:\n{auction_id_ssp}")
    #ad_response = {**ad_response_adx}
    ad_response = {
        "adx_id": adx_id,
        "auction_id_adx": str(uuid4())[:8],
        "auction_id_ssp": auction_id_ssp,
        "bid_amount": round(uniform(0, 6), 2),
        "creative_url": f"{adx_id} mock ad url",
        "categories": categories,
        "ttl": choice([5, 10, 15]),
        "render_beacon": f"beacon_{adx_id}",
    }
    AdResponseADX.model_validate(ad_response)
    #return ad_response  
    return  AdResponseADX(**ad_response)


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


async def adx_ad_request(
    request: Request, payload: AdRequestSSP, x_api_key: str = Header()
):
    #if random() < 0.1:
     #   return Response(status_code=status.HTTP_204_NO_CONTENT)
    adx_id = request.url.path[-1]

    if x_api_key != test_api_key:
        if x_api_key not in valid_api_keys:
            raise HTTPException(status_code=401, detail="Invalid API key")

        if valid_api_keys[x_api_key]["adx_id"] != adx_id:
            raise HTTPException(
                status_code=403, detail="API key doesn't match this adx"
            )
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
    logger.debug(f"auction_id_ssp:\n{auction_id_ssp}")
    ad_response = {
        "adx_id": adx_id,
        "auction_id_adx": str(uuid4())[:8],
        "auction_id_ssp": auction_id_ssp,
        "bid_amount": round(uniform(0, 6), 2),
        "creative_url": f"{adx_id} mock ad url",
        "categories": categories,
        "ttl": choice([5, 10, 15]),
        "render_beacon": f"beacon_{adx_id}"
    }
    try:
        AdResponseADX.model_validate(ad_response)
        return AdResponseADX(**ad_response)
    except ValidationError as e:
        logger.error(str(e))
