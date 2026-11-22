from random import choice, randint

from .generator_user import generate_user


class User:
    def __init__(self):
        self.data = generate_user().model_dump()
        self.request_limit = randint(75, 150)
        self.request_counter = 0

    def is_exhausted(self):
        return self.request_counter >= self.request_limit

    def increment_request_counter(self):
        self.request_counter += 1


_user_pool = []

def pick():
    try:
        return choice(_user_pool)
    except IndexError:
        user = User()
        _user_pool.append(user)
        return user

def user_exhaust_check(user: User):
    if user.is_exhausted():
        try:
            _user_pool.remove(user)
        except ValueError:
            pass # We don't really care for users, so there is no need to fight racing
        _user_pool.append(User())
    

def populate_user_pool(population: int = 10000):
    _user_pool.clear()
    _user_pool.extend(User() for _ in range(population))
