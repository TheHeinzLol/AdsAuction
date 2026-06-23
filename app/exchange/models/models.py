import uuid

from datetime import datetime
from sqlalchemy import DateTime, Float, Integer, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Auction(Base):
    __tablename__ = "auctions"
    id: Mapped[int] = mapped_column(primary_key = True)
    winner: Mapped[uuid.UUID] = mapped_column(
            Uuid(as_uuid=True, native_uuid=True),
            nullable=True,
            default=None
            )
    winning_bid: Mapped[float] = mapped_column(Float, nullable=True)
    time_created: Mapped[datetime] = mapped_colum(
            DateTime(timezone=True),
            nullable=False
    time_closed: Mapped[datetime] = mapped_colum(
            DateTime(timezone=True),
            nullable=False
            )
    
