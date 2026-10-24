from pydantic import BaseModel, ConfigDict


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


class AuctionSSP(BaseModel):
    auction_id_ssp: str
    adx_id: str
    auction_id_adx: str
    bid_amount: float
    publisher_id: str
    categories: list[str]
