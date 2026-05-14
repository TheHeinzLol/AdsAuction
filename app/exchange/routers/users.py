from datetime import timedelta
from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select, insert

from ..auth.authentification import (
        create_access_token,
        hash_password,
        oauth2_scheme,
        verify_access_token,
        verify_password
        )
from ..core.config import settings
from ..database.database import Base, DBSession, engine #base and engine are for recreating db after drop
from ..models.models import User, Auction
from ..schemas.schemas import Token, UserCreateSchema, UserResponseSchema

import uuid

router = APIRouter()

@router.post('/',
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

@router.post('/token', response_model=Token)
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
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Incorrect email or password",
                headers={'WWW-Authenticate': 'Bearer'},
                )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
            data={'sub': str(user.id)},
            expires_delta=access_token_expires,
            )
    return Token(access_token=access_token, token_type='bearer')

@router.get('/me', response_model=UserResponseSchema)
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

@router.get('/draft')
def draft(db: DBSession, minimal_bid=0):

    result = db.execute(select(User).where(User.account_balance >= minimal_bid))
    bidders = result.scalars().all()
    return {'type': bidders}

# Debug section
from pydantic import BaseModel
class TableDropSchema(BaseModel):
    table: str

@router.post('/populate')
def populate_user_db(db: DBSession):
    from random import uniform
    logins = ['admin', 'ass', 'twat', 'asstwat', 'poopoo', 'peepee', 'foo', 'baz', 'bar',
              'rkelly', 'JoeBiden', 'JennyTalia']
    email_postfix = "@fakemail.com"
    users_to_insert = []
    for login in logins:
        result = db.execute(
                select(User)
                .where(
                    func.lower(User.login) == login.lower()
                    or func.lower(User.email) == (login+email_postfix).lower()
                       )
                )
        existing_user = result.scalars().first()
        if existing_user:
            continue
        users_to_insert.append(
                {
                    'login': login,
                    'email': login+email_postfix,
                    'password_hash': hash_password(login),
                    'account_balance': round(uniform(0, 100), 2)
                }
            )
    if len(users_to_insert) > 0:
        db.execute(insert(User), users_to_insert)
        db.commit()
    return {'users inserted': len(users_to_insert)}

@router.post('/drop_table')
def drop_table(db: DBSession, payload: TableDropSchema):
    from sqlalchemy import text
    table = payload.table
    with db.get_bind().connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
        conn.commit()
    print(f"table {table} dropped")
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully")
    except Exception as e:
        print(f"Failed to create tables: {e}")
    return {'dropped': table}

# populating
class PopulateRandomSchema(BaseModel):
    insert_number: int

@router.post('/populate_db')
def populate_db(db: DBSession, payload: PopulateRandomSchema):
    import random
    import string
    from sqlalchemy import insert
    insert_number = payload.insert_number
    def generate_login(login_min_length: int, login_max_length: int) -> str:
#generate a random login of 3-20 length characters, including letters and digits
        random_login = ''.join(random.choices(
            string.ascii_letters + string.digits, 
            k=random.choice(range(login_min_length, login_max_length+1))
            )
         )
        return random_login

    logins = [generate_login(3,20) for i in range(1, insert_number+1)]

    def generate_user(login:str) -> UserCreateSchema:
        user = {
                'login': login,
                'email': login+"@fakemail.com",
                'password_hash': hash_password(login),
                'account_balance': round(random.uniform(0, 100), 2)
                }
        return user

    users = [generate_user(login) for login in logins]
    print(users[:5])

    from typing import List
    def populate_db(
            db: DBSession,
            logins: List[str],
            users: List[UserCreateSchema]
            ):
        db.execute(insert(User), users)
        db.commit()
        print("db populated")
    
    print(f"Populating db with {insert_number} users")
    populate_db(db, logins, users)

    return {'populated': insert_number}


