
import uuid

from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Auction(Base):
    __tablename__ = "ssp_auctions"
    auction_id: Mapped[str] = mapped_column(Uuid(as_uuid=True, native_uuid=True), primary_key=True)
    time_created: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    time_closed: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    publisher_id: Mapped[str] = mapped_column(String, nullable=False)
    winner: Mapped[str] = mapped_column(String)
    winner_bid: Mapped[float] = mapped_column(Float)
    is_rendered: Mapped[bool] = mapped_column(Boolean)

    bids: Mapped[list['Bid']] = relationship(back_populates="auction")
    

class Bid(Base):
    __tablename__ = "bids"
    id: Mapped[int] = mapped_column(primary_key=True)
    auction_id: Mapped[uuid.UUID] = mapped_column(
            ForeignKey('ssp_auctions.auction_id'),
            unique=False,
            nullable=False,
            )
    time_sent: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    time_received: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    adx_id: Mapped[str] = mapped_column(String, nullable=False)
    creative_url: Mapped[str] = mapped_column(String, nullable=False)
    bid_amount: Mapped[float] = mapped_column(Float, nullable=False)
    is_winning: Mapped[bool] = mapped_column(Boolean, nullable=False)
    categories: Mapped[list] = mapped_column(ARRAY(String), nullable=False)

    auction: Mapped['Auction'] = relationship(back_populates="bids")

    __table_args__ = (
        CheckConstraint("bid_amount > 0", name="bid_amount_positive"),
    )
