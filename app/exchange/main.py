import aiohttp
from fastapi import FastAPI

from contextlib import asynccontextmanager
from app.exchange.database.database import async_engine, DBSession
from app.exchange.middleware.metrics import setup_prometheus
from app.exchange.models.models import Base
from app.exchange.routers.ssp import router as ssp_router

API_KEYS = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    #create tables in postgres
    try:
        async with async_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"Failed to create tables: {e}")
    # get the api keys
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://dsp_fapi:8001/get_api_keys') as response:
                app.state.api_keys = await response.json()
                if response.status != 200:
                    app.state.api_keys = {
                        'spare_key':{
                            'key':'my_spare_key',
                            'created_at': datetime.now(timezone.utc).isoformat()
                            }
                        }
                    print(f"get_api_keys response: {app.state.api_keys}")
    except Exception as e:
        print(f"Failed fetch api keys: {e}")

    yield

app = FastAPI(title="Exchange FastAPI", lifespan=lifespan)
setup_prometheus(app)

app.include_router(ssp_router)

@app.get('/')
def get_root():
    return {'this':"is index page"}

@app.get('/healthz')
def health_check():
    return {"status": "healty"}

@app.get('/check_keys')
def keys():
    return app.state.api_keys
