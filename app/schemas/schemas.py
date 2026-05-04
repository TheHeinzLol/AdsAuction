from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

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
