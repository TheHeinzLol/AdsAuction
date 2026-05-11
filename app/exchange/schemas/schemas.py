from datetime import datetime
from pydantic import AfterValidator, BaseModel, EmailStr, Field
from typing import Annotated

# SSP schemas
class SSPUserInfoSchema(BaseModel):
    """Schema for validation of a user info sent to
    exchange service by the SSP"""
    timestamp: datetime
    region: str
    language: str
    device: str
    channel: str
    category: str

class SSPResponseSchema(SSPUserInfoSchema):
    """Same data which exchange got but with ads URL"""
    ad_url: str

class UserBaseSchema(BaseModel):
    email: EmailStr = Field(max_length=50)
    login: str = Field(min_length=3, max_length=20)

class UserCreateSchema(UserBaseSchema):
    password: str = Field(min_length=3, max_length=16)

class UserResponseSchema(UserBaseSchema):
    date_created: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
