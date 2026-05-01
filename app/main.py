from datetime import datetime
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import Annotated

from app.database.models import User
from app.database.database import Base, engine, get_db, SessionLocal


Base.metadata.create_all(bind=engine)

DBSession = Annotated[Session, Depends(get_db)]

app = FastAPI()

from pydantic import BaseModel
class UserCreateSchema(BaseModel):
    email: str
    login: str
    password: str

class UserResponseSchema(BaseModel):
    email: str
    login:str
    date_created: datetime


@app.get('/')
def get_root(db: DBSession):
    return {'this':"is index page"}


# routing
# from fastapi import Response, status, HTTPException #Response.status_code = status.HTTP_code_desc
# or raise HTTPException(status_code=status.HTTP_code_desc, detail="your description"
# If deleting, return Response(status_code=status.HTTP_204_NO_CONTENT
from fastapi import status
@app.post('/',
          status_code=status.HTTP_201_CREATED,
          response_model=UserResponseSchema
          )
def create_user(db: DBSession, payload: UserCreateSchema):
    new_user = User(
            login=payload.login,
            email=payload.email,
            password=payload.password
            )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
