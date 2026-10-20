"""
Tests for user_pool.py
Checks methods for user and pool consistency under operations.
"""

import pytest

from OWS.src.user_pool import populate_user_pool, User, USER_POOL, user_exhaust_check


@pytest.fixture(autouse=True)
def clear_pool():
    """Clear queue."""
    USER_POOL.clear()
    yield
    USER_POOL.clear()


def test_user_pool_populating():
    populate_user_pool(10)
    assert len(USER_POOL) == 10


def test_user_increment_request_counter():
    user = User()
    user.increment_request_counter()
    assert user.request_counter == 1


def test_user_is_exhausted():
    user = User()
    user.request_limit = 1
    assert user.is_exhausted() == False
    user.increment_request_counter()
    assert user.is_exhausted() == True


def test_user_exhaustion_check():
    populate_user_pool(1)
    user = USER_POOL[0]
    user.request_limit = 1
    user_exhaust_check(user)
    assert USER_POOL[0] == user
    user.increment_request_counter()
    user_exhaust_check(user)
    assert USER_POOL[0] != user
