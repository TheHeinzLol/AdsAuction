from datetime import datetime
from random import uniform
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy import CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
import uuid

from ..database.database import Base

class User(Base):
    __tablename__ = 'users'
    __table_args__ = (
            # These checks are redundant due to pydantic validation.
            # But I will leave it here in case I will change the fact
            # that users table will only be changed with http calls
            # for registration or profile editing
            CheckConstraint('char_length(login) > 2', name='login_min_length_check'),
            )

    id: Mapped[uuid.UUID] = mapped_column(
            # Postgres natively supports UUID type
            # Hence, native_uuid
            Uuid(as_uuid=True, native_uuid=True),
            primary_key=True,
            default=uuid.uuid4
            )
    login: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    date_created: Mapped[datetime] = mapped_column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now()
        )
    account_balance: Mapped[float] = mapped_column(Float,
                                                  unique=False,
                                                  nullable=False,
                                                  default=round(uniform(0, 100), 2)
                                                  )

    auctions_won: Mapped[List['Auction']] = relationship(back_populates='winner')

class Auction(Base):
    __tablename__ = 'auctions'

    id: Mapped[str] = mapped_column(
            Uuid(as_uuid=True, native_uuid=True),
            primary_key=True,
            default=uuid.uuid4
            )
    winner_id: Mapped[uuid.UUID] = mapped_column(
            ForeignKey('users.id'),
            unique=False,
            nullable=True
            )
    winning_bid: Mapped[float] = mapped_column(Float, unique=False, nullable=True)
    date_started: Mapped[datetime] = mapped_column(
            DateTime(timezone=True),
            nullable=False,
            default=datetime.utcnow()
            )

    winner: Mapped['User'] = relationship(back_populates='auctions_won')

