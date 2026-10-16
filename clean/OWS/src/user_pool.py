
from random import randint
from uuid import uuid4
from .generator_user import generate_user

class User:
    def __init__(self):
        self.data = generate_user()
        self.request_limit = randint(75, 150)
        self.request_counter = 0

    def is_exhausted(self):
        if self.request_counter >= self.request_limit:
            return True
        else:
            return False

    def increment_request_counter(self):
        self.request_counter += 1

USER_POOL = []

def user_exhaust_check(user: User):
    if user.is_exhausted():
        USER_POOL.remove(user)
        USER_POOL.append(User())

def populate_user_pool(population: int=10000):
    USER_POOL.clear()
    USER_POOL.extend(User() for _ in range(population))

