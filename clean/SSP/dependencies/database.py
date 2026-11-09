
import os
from fastapi import Depends
from typing import Annotated
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DATABASE_URL = os.getenv('SSP_DB_URL', "postgresql+psycopg://admin:admin@localhost:5433/database_ssp")
#async engine for everything else
async_engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,           # Keep 20 connections open
    max_overflow=20,        # Allow up to 20 extra if needed
    pool_pre_ping=True,     # Verify connections are alive
    #echo=False              # Turn off SQL logging for production
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

