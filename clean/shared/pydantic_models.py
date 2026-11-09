from pydantic import BaseModel, ConfigDict
from datetime import datetime


class AdRequestCommon(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str
    category: str
    floor_price: float  # temp until publisher policy is implemented
    device: str
    channel: str
    ad_size: tuple[int, int] | None
    region: str
    languages: list[str]
    local_hour: int


class AdRequestOWS(AdRequestCommon):
    publisher_id: str


class AdRequestSSP(AdRequestCommon):
    auction_id_ssp: str


class AdResponseSSP(BaseModel):
    model_config = ConfigDict(extra="forbid")

    auction_id_ssp: str
    ad_url: str
    ttl: int


class AdResponseADX(AdResponseSSP):
    adx_id: str
    auction_id_adx: str
    bid_amount: float
    categories: list[str]

class AuctionsSSP(BaseModel):
    auction_id: str
    time_created: datetime
    time_closed: datetime
    publisher_id: str
    winner: str
    winner_bid: float
    is_rendered: bool

class BidsSSP(BaseModel):
    auction_id: str
    time_sent: datetime
    time_received: datetime
    adx_id: str
    creatve_url: str
    bid_amount: str
    categories: list[str]
    is_winning: bool

