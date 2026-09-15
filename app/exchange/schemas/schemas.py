from pydantic import BaseModel

# SSP schemas
class SSPUserInfoSchema(BaseModel):
    """Schema for validation of a user info sent to
    exchange service by the SSP"""
    id: int
    local_hour: int
    region: str
    languages: list[str]
    device: str
    channel: str
    categories: list[str]
    ad_size: list[int] | None

class SSPResponseSchema(BaseModel):
    """Same data which exchange got but with ads URL"""
    ad_url: str
    burl: str


