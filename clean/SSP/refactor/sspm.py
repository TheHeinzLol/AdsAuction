
import asyncio
import logging
import os
from contextlib import asynccontextmanager

from dependencies.database import async_engine
from dependencies.redis import close_redis, get_redis
from fastapi import FastAPI, Response, status
from models.models import Base
from src.worker_insert import worker_insert
from src.worker_render import worker_render

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s [%(funcName)s]:\n%(message)s",
    force=True
)
logging.getLogger("src.worker_insert").setLevel(logging.DEBUG)
logging.getLogger("src.worker_render").setLevel(logging.DEBUG)

METRICS_PORT = int(os.getenv("METRICS_PORT", "8041"))
CONCURRENCY = 150
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Get redis instance
    try:
        app.state.redis = await get_redis()
        logger.info("Redis initialized")
    except Exception as e:
        logger.error(f"Failed to get redis:\n{e}")
    # Create tables in postgres. Won't recreate if tables are already there.
    try:
        await create_database_tables()
        logger.info("Success: database tables created")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
    app.state.semaphore = asyncio.Semaphore(CONCURRENCY)
    workers = [
        asyncio.create_task(worker_insert(app.state.redis), name="insert"),
        asyncio.create_task(worker_render(app.state.redis), name="render")
        ]
    yield
    # stop workers
    for worker in workers: 
        worker.cancel()
        logger.info(f"Cancelling {worker.get_name()} worker")
    # close connections

    await close_redis()
    
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return Response(status_code=status.HTTP_200_OK)

# Helper functions
async def create_database_tables():
    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
