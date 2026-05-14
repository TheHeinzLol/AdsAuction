import os
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from typing import Annotated

DATABASE_URL = os.getenv('DATABASE_URL')
#engine = create_engine(DATABASE_URL)

engine = create_engine(
    DATABASE_URL,
    pool_size=10,           # Keep 10 connections open
    max_overflow=20,        # Allow up to 20 extra if needed
    pool_pre_ping=True,     # Verify connections are alive
    echo=False              # Turn off SQL logging for production
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    with SessionLocal() as db:
        try:
            yield db
        finally:
            db.close()

DBSession = Annotated[Session, Depends(get_db)]
