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
#    creative_url: str
    bid_amount: float
    categories: list[str]

class BidSSP(AdResponseADX):

    time_sent: float
    time_received: float
    is_winning: bool

class ModelAuctionsSSP(BaseModel):
    auction_id: str
    time_created: float
    time_closed: float
    publisher_id: str
    winner: str | None
    winner_bid: float | None
    is_rendered: bool

class ModelBidsSSP(BaseModel):
    auction_id: str
    time_sent: float
    time_received: float
    adx_id: str
    creative_url: str
    bid_amount: float
    categories: list[str]
    is_winning: bool

