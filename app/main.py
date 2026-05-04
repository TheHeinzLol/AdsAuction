from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import Annotated

from app.database.database import Base, engine, get_db
from app.models.models import User

try:
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully")
except Exception as e:
    print(f"Failed to create tables: {e}")

DBSession = Annotated[Session, Depends(get_db)]

app = FastAPI()

# routing
# from fastapi import Response, status, HTTPException #Response.status_code = status.HTTP_code_desc
# or raise HTTPException(status_code=status.HTTP_code_desc, detail="your description"
# If deleting, return Response(status_code=status.HTTP_204_NO_CONTENT
from datetime import datetime
from fastapi import status, HTTPException
from sqlalchemy import func, select

from app.schemas.schemas import UserCreateSchema, UserResponseSchema

@app.get('/')
def get_root(db: DBSession):
    return {'this':"is index page"}

@app.post('/',
          status_code=status.HTTP_201_CREATED,
          response_model=UserResponseSchema
          )
def create_user(db: DBSession, payload: UserCreateSchema):
   
    result = db.execute(
            select(User).where(func.lower(User.login) == payload.login.lower()),
            )
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Login already taken",
                )
    
    result = db.execute(
            select(User).where(func.lower(User.email) == payload.email.lower()),
            )
    existing_email = result.scalars().first()
    if existing_email:
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken",
                )

    new_user = User(
            login=payload.login.strip(),
            email=payload.email.lower().strip(),
            password_hash=hash_password(payload.password)
            )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm

import uuid

from app.schemas.schemas import Token
from app.core.config import settings
from app.auth.authentification import (
        create_access_token,
        hash_password,
        oauth2_scheme,
        verify_access_token,
        verify_password
)
@app.post('/token', response_model=Token)
def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: DBSession
        ):

    result = db.execute(
            select(User).where(
                func.lower(User.email) == form_data.username.lower(), #oauth uses email as username
                ),
            )
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={'WWW-Authenticate': 'Bearer'},
                )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
            data={'sub': str(user.id)},
            expires_delta=access_token_expires,
            )
    return Token(access_token=access_token, token_type='bearer')

@app.get('/me', response_model=UserResponseSchema)
def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        db: DBSession
        ):
    """Get currently authenticated user."""
    headers={'WWW-Authenticate': 'Bearer'}

    # Verify token
    user_id = verify_access_token(token)
    if user_id is None:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers=headers,
                )
    # Validate UUID format
    try:
        user_uuid = uuid.UUID(user_id, version=4)
    except ValueError:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers=headers,
                )
    
    # Fetch user
    result = db.execute(
            select(User).where(User.id == user_uuid),
            )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers=headers,
                )
    return user

