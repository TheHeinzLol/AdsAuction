import aiohttp
from fastapi import FastAPI

from contextlib import asynccontextmanager
from app.exchange.dependencies.database import async_engine
from app.exchange.dependencies.redis import close_redis, get_redis
from app.exchange.middleware.metrics import setup_prometheus
from app.exchange.models.models import Base
from app.exchange.routers.ssp import router as ssp_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # create tables in postgres
    try:
        async with async_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"Failed to create tables: {e}")

    # get redis client
    app.state.redis = await get_redis()

    # get the api keys
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://dsp_fapi:8001/get_api_keys') as response:
                api_keys = await response.json()
                if response.status != 200:
                    api_keys = {
                        'spare_key':{
                            'key':'my_spare_key',
                            'created_at': datetime.now(timezone.utc).isoformat()
                            }
                        }
                    print(f"get_api_keys response: {app.state.api_keys}")
    except Exception as e:
        print(f"Failed fetch api keys: {e}")
    # save keys to redis
    try:
        for dsp_id, key_info in api_keys.items():
            await app.state.redis.hset("dsp:api_keys", dsp_id, key_info["key"])
    except Exception as e:
       print(f"failed to save keys to Redis: {e}")

    yield
    
    await close_redis()

app = FastAPI(title="Exchange FastAPI", lifespan=lifespan)
setup_prometheus(app)

app.include_router(ssp_router)
@app.get('/')
def get_root():
    return {'this':"is index page"}

@app.get('/healthz')
def health_check():
    return {"status": "healty"}

