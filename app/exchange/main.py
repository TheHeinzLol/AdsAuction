from fastapi import FastAPI

from contextlib import asynccontextmanager
from .database.database import async_engine, DBSession
from .middleware.metrics import setup_prometheus
from .models.models import Base
from .routers.users import router as users_router
from .routers.auctions import router as auctions_router
from .routers.ssp import router as ssp_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with async_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"Failed to create tables: {e}")
    yield

app = FastAPI(title="Exchange FastAPI", lifespan=lifespan)
setup_prometheus(app)

app.include_router(users_router)
app.include_router(auctions_router)
app.include_router(ssp_router)

@app.get('/')
def get_root(db: DBSession):
    return {'this':"is index page"}

@app.get('/healthz')
def health_check():
    return {"status": "healty"}

