from datetime import datetime
from fastapi import APIRouter
from sqlalchemy import select, update, desc

from app.database.database import DBSession
from app.models.models import User, Auction

router = APIRouter()

@router.get('/test')
def auc_test(db: DBSession):
    return {'status': 'ok'}

@router.get('/run_auction')
def run_auction(db: DBSession, minimal_bid: float = 0.0):
    from random import uniform
    date_started = datetime.utcnow()
    result = db.execute(
                        select(User)
                        .where(User.account_balance >= minimal_bid)
                        .order_by(desc(User.account_balance))
                        )
    bidders = result.scalars().all()
    # if no suitable bidders, close auction with no winner and winning bid
    if not bidders:
        new_auction = Auction(
                winner_id=None,
                winning_bid=None,
                date_started=date_started
                )
    else:
        # generating bids for all bidders
        for bidder in bidders:
            bidder.bid = round(uniform(minimal_bid, min(3, bidder.account_balance)), 2)
        # determining a winner
        winning_bid = minimal_bid 
        for bidder in bidders:
            if bidder.bid > winning_bid:
                winning_bid = bidder.bid
                winner = bidder
        print(winner.bid, winner.login, winner.account_balance)
        # inserting a record
        new_auction = Auction(
                winner_id=winner.id,
                winning_bid=winner.bid,
                date_started=date_started
                )
    db.add(new_auction)
    db.commit()
    # edit winner's balance
    db.execute(
               update(User)
               .where(User.id == winner.id)
               .values(account_balance=User.account_balance-winning_bid)
               )
    db.commit()

