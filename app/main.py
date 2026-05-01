from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import Annotated

from app.database.models import Base
from app.database.database import engine, get_db, SessionLocal


Base.metadata.create_all(bind=engine)
DBSession = Annotated[Session, Depends(get_db)]

app = FastAPI()

from pydantic import BaseModel
class User(BaseModel):
    email: str
    login: str
    password: str


@app.get('/')
def get_root(db: DBSession):
    return {'this':"is index page"}


# routing
# from schemas/models import User
# from fastapi import Response, status, HTTPException #Response.status_code = status.HTTP_code_desc
# or raise HTTPException(status_code=status.HTTP_code_desc, detail="your description"
# If deleting, return Response(status_code=status.HTTP_204_NO_CONTENT
from fastapi import status
@app.post('/', status_code=status.HTTP_201_CREATED)
def create_user(db: DBSession, payload: User):
    pass
