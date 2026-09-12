import asyncio
import logging

from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from redis import asyncio as aioredis

from app.exchange.dependencies.redis import close_redis, get_redis
from app.exchange.middleware.metrics import setup_prometheus
from app.exchange.routers.ssp import router as ssp_router
from app.exchange.scripts.insert_worker import bulk_insert

@asynccontextmanager
async def lifespan(app: FastAPI):
    # create tables in postgres
    await create_database_tables()
    # get redis client
    app.state.redis = await get_redis()
    # get the api keys
    api_keys = await fetch_api_keys()
    # save keys to redis
    await save_keys_to_redis(app.state.redis, api_keys)
    app.state.workers = {
            #this one is to do: replace api keys fetch with this
#            "worker: api keys update": asyncio.create_task(
#                update_api_keys(app.state.redis)
        "insert": asyncio.create_task(bulk_insert(app.state.redis))
        }
    yield
    # close redis at shutdown
    await close_redis()

app = FastAPI(title="Exchange FastAPI", lifespan=lifespan)
setup_prometheus(app)
app.include_router(ssp_router)

@app.get('/')
def get_root():
    return {'this':"is index page"}

@app.get('/healthz')
def health_check():
    return {"status": "healthy"}

@app.get('/update_keys')
async def update_keys(request: Request):
    """Manually refresh API keys from DSP without restarting."""
    api_keys = await fetch_api_keys()
    await save_keys_to_redis(request.app.state.redis, api_keys)
    return {"status": "keys updated", "keys_loaded": len(api_keys)}

# Helper functions
async def create_database_tables():
    from app.exchange.dependencies.database import async_engine
    from app.exchange.models.models import Base
    try:
        async with async_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        print("Success: database tables created")
    except Exception as e:
        print(f"Failed to create tables: {e}")

async def fetch_api_keys() -> dict:
    import aiohttp
    from datetime import datetime, timezone
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://dsp_fapi:8001/get_api_keys') as response:
                api_keys = await response.json()
                if response.status == 200:
                    print("Success: fetched api keys")
                    return api_keys  
                else:       
                    print(f"Failed fetch_api_keys response: {api_keys}")
    except Exception as e:
        print(f"Failed to fetch api keys: {e}")
    
    return {
            'spare_key':{
                'key':'my_spare_key',
                'created_at': datetime.now(timezone.utc).isoformat()
                }
            }

async def save_keys_to_redis(redis: aioredis.Redis, api_keys: dict):
    try:
        for key, dsp_id in api_keys.items():
            print(dsp_id, key)
            await redis.hset("dsp:api_keys", dsp_id["dsp"], key)
        print("Success: saved api keys to redis cache")
    except Exception as e:
       print(f"Failed to save keys to Redis: {e}")
# End of Helper functions

