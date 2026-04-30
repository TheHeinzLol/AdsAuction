from fastapi import Body, FastAPI
from pydantic import BaseModel
from typing import Annotated

app = FastAPI()

class User(BaseModel):
    email: str
    login: str
    password: str

users: list[dict] = []

@app.get('/')
def get_root():
    return {'fuck':'you'}

@app.post('/')
def create_user(payload: User):
    user_data = {
            'email': payload.email,
            'login': payload.login,
            'password': payload.password
            }
    users.append(user_data)
    return {
            'message': "you've created an account",
            'email': payload.email,
            'login': payload.login
            }
