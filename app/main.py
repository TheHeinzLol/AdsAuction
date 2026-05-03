from datetime import datetime
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import Annotated

from app.database.database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

DBSession = Annotated[Session, Depends(get_db)]

app = FastAPI()


@app.get('/')
def get_root(db: DBSession):
    return {'this':"is index page"}


# routing
# from fastapi import Response, status, HTTPException #Response.status_code = status.HTTP_code_desc
# or raise HTTPException(status_code=status.HTTP_code_desc, detail="your description"
# If deleting, return Response(status_code=status.HTTP_204_NO_CONTENT
from app.schemas.schemas import UserCreateSchema, UserResponseSchema
from app.models.models import User
from fastapi import status
@app.post('/',
          status_code=status.HTTP_201_CREATED,
          response_model=UserResponseSchema
          )
def create_user(db: DBSession, payload: UserCreateSchema):
    
    payload_dict = payload.model_dump()
    new_user = User(**payload_dict)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

