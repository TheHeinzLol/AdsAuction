"""
Tests for user_pool.py
Checks methods for user and pool consistency under operations.
"""

import pytest

from OWS.src.user_pool import User, _user_pool, populate_user_pool, user_exhaust_check


@pytest.fixture(autouse=True)
def clear_pool():
    """Clear queue."""
    _user_pool.clear()
    yield
    _user_pool.clear()


def test_user_pool_populating():
    populate_user_pool(10)
    assert len(_user_pool) == 10


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
    user = _user_pool[0]
    user.request_limit = 1
    user_exhaust_check(user)
    assert _user_pool[0] == user
    user.increment_request_counter()
    user_exhaust_check(user)
    assert _user_pool[0] != user
