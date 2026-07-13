import uuid

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Auction(Base):
    __tablename__ = "auctions"
    id: Mapped[str] = mapped_column(
            Uuid(as_uuid=True, native_uuid=True),
            primary_key=True
        )
    winner: Mapped[str] = mapped_column(String)
    winning_bid: Mapped[float] = mapped_column(Float)
    time_created: Mapped[datetime] = mapped_column(
            DateTime(timezone=True),
            nullable=False
            )
    time_closed: Mapped[datetime] = mapped_column(
            DateTime(timezone=True),
            nullable=False
            )
    user_context: Mapped[str] = mapped_column(JSONB)

    bids: Mapped[list('Bid')] = relationship(back_populates="auction")

class Bid(Base):
    __tablename__ = "bids"
    id: Mapped[int] = mapped_column(primary_key=True)
    auction_id: Mapped[uuid.UUID] = mapped_column(
            ForeignKey('auctions.id'),
            unique=False,
            nullable=False,
            )
    time_sent: Mapped[datetime] = mapped_column(
            DateTime(timezone=True),
            nullable=False
            )
    time_ms_response: Mapped[int] = mapped_column(Integer, nullable=False)
    bid_amount: Mapped[float] = mapped_column(Float, nullable=False)
    is_winning: Mapped[bool] = mapped_column(Boolean, nullable=False)
    dsp_url: Mapped[str] = mapped_column(String, nullable=False)

    auction: Mapped['Auction'] = relationship(back_populates="bids")

