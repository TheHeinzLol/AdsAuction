import pytest
import time
from OWS.src.delayed_queue import _delayed_queue as queue
from OWS.src.delayed_queue import schedule, peek, pop, size


@pytest.fixture(autouse=True)
def clear_queue():
    """Clear queue."""
    queue.clear()
    yield
    queue.clear()


# ===== schedule =====


def test_adds_item():
    schedule(auction_id="foo", ttl=1)
    assert len(queue) == 1


def test_schedule_increases_size():
    assert len(queue) == 0

    schedule(auction_id="foo", ttl=1)
    assert len(queue) == 1

    schedule(auction_id="bar", ttl=1)
    assert len(queue) == 2


def test_schedule_stores_auction_id():
    schedule(auction_id="foo", ttl=1)
    assert queue[0][1] == "foo"


def test_schedule_sets_correct_send_at():
    ttl = 10
    before = time.time()
    schedule(auction_id="foo", ttl=ttl)
    after = time.time()
    assert before + ttl <= queue[0][0] <= after + ttl


# ===== peek =====


def test_peek_returns_none_on_empy_queue():
    assert peek() is None


def test_peek_returns_earliest_item():
    schedule(auction_id="later", ttl=10)
    schedule(auction_id="sooner", ttl=1)

    item = peek()
    assert item is not None
    assert item[1] == "sooner"


def test_peek_does_not_remove_item():
    schedule(auction_id="foo", ttl=1)
    peek()
    assert len(queue) == 1


def test_peek_returns_same_item_on_repeated_calls():
    schedule(auction_id="foo", ttl=1)
    schedule(auction_id="bar", ttl=10)
    first = peek()
    second = peek()
    assert first == second


# ===== pop =====


def test_pop_returns_none_on_empty_queue():
    assert pop() is None


def test_pop_deletes_item_from_queue():
    schedule(auction_id="foo", ttl=1)
    schedule(auction_id="bar", ttl=10)
    pop()
    assert len(queue) == 1


def test_pop_returns_returns_earliest_item():
    schedule(auction_id="later", ttl=10)
    schedule(auction_id="sooner", ttl=1)
    item = pop()
    assert item[1] == "sooner"


def test_pop_returns_items_in_order():
    schedule(auction_id="c", ttl=10)
    schedule(auction_id="a", ttl=1)
    schedule(auction_id="b", ttl=5)

    assert pop()[1] == "a"
    assert pop()[1] == "b"
    assert pop()[1] == "c"


# ===== size =====


def test_size_returns_correct_size():
    assert size() == 0
    schedule(auction_id="c", ttl=10)
    assert size() == 1
    schedule(auction_id="a", ttl=1)
    assert size() == 2
    schedule(auction_id="b", ttl=5)
    assert size() == 3
