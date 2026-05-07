

router = APIRouter()
DBSession = Annotated[Session, Depends(get_db)]

@router.get('/run_auction')
def run_auction(db: DBSession, minimal_bid: float):
    date_started = datetime.utcnow()
    result = db.execute(
                        select(User)
                        .where(User.account_balance >= minimal_bid)
                        .order_by(desc(User.account_balance))
                        .limit(1)
                        )
    bidders = result.scalars().all()
    if not bidders:
        new_auction = Auction(
                winner_id=None,
                winning_bid=None,
                date_started=date_started
                )


