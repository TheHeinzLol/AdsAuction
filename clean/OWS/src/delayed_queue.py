import heapq
import logging
import time

_delayed_queue: list[tuple[float, str]] = []

logger = logging.getLogger(__name__)

def schedule (
        auction_id: str,
        ttl: float
) -> None:
    """Add item into the delaed queue."""
    send_at = time.time() + ttl
    heapq.heappush(_delayed_queue, (send_at, auction_id))
    logger.debug(f"Queued responses: {len(_delayed_queue)}")

def peek() -> tuple[float, str] | None:
    """Look at the next item without deleting it."""
    if not _delayed_queue:
        return None
    return _delayed_queue[0]

def pop() -> tuple[float, str] | None:
    """Remove and return next item."""
    if not _delayed_queue:
        return None
    return heapq.heappop(_delayed_queue)

def size() -> int:
    """Return current queue size."""
    return len(_delayed_queue)

