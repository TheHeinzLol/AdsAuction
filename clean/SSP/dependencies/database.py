
import os
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = 5433 if POSTGRES_HOST == "localhost" else 5432
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "admin")
POSTGRES_USER = os.getenv("POSTGRES_USER", "admin")
POSTGRES_DB = os.getenv("POSTGRES_DB", "database_ssp")

DATABASE_URL = os.getenv(
        'SSP_DB_URL', 
        f"postgresql+psycopg://"
        f"{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)
#async engine for everything else
async_engine = create_async_engine(
    DATABASE_URL,
    pool_size=50,           # Keep 50 connections open
    max_overflow=20,        # Allow up to 20 extra if needed
    pool_pre_ping=True,     # Verify connections are alive
)

SessionLocal = async_sessionmaker(
        bind=async_engine,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )

async def get_db():
    async with SessionLocal() as db:
        try:
            yield db
        except Exception:
            await db.rollback()
            raise
        finally:
            await db.close()

DBSession = Annotated[AsyncSession, Depends(get_db)]

