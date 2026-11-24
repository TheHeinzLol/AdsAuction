import asyncio
import logging
import time

import aiohttp

from .delayed_queue import _delayed_queue as queue
from .delayed_queue import peek
from .metrics import RENDERS_CONFIRMED

logger = logging.getLogger(__name__)

async def worker_render(
        stop: asyncio.Event,
        url: str,
        concurrency: int
):
    connector = aiohttp.TCPConnector(enable_cleanup_closed=True)
    async with aiohttp.ClientSession(connector=connector) as session:
        await render_ad(session, stop, url, concurrency)


async def render_ad(session: aiohttp.ClientSession, stop: asyncio.Event, url: str, concurrency: int):
    """
    Perpetually checks for items in queue to send render confirmation.
    Waits 0.1s if queue is empty.
    """
    semaphore = asyncio.Semaphore(concurrency)
    while not stop.is_set():
        item = peek()
        if item is None:
            await asyncio.sleep(0.1)
            continue

        send_at, auction_id = item
        now = time.time()
        if send_at <= now:
            logger.debug(f"sending item {item}")
            queue.remove(item)
            try:
                await send_render_confirmation(
                    session=session, url=url, auction_id=auction_id, semaphore=semaphore
                )
            except Exception as e:
                logger.info(f"\nFailed render confirmation request. Error:\n{e}\n")
        else:
            await asyncio.sleep(min(send_at - now, 0.1))


async def send_render_confirmation(
        session: aiohttp.ClientSession, url: str, auction_id: str, semaphore: asyncio.locks.Semaphore
) -> None:
    async with session.post(
        url=url, json={"auction_id_ssp": auction_id}
    ) as response:
        if response.status not in [200, 204]:
            response_body = await response.json()
            logger.info(f"\nFailed to confirm rendering. Response:\n{response_body}")
        else:
            RENDERS_CONFIRMED.inc()
            logger.debug(f"\nRender confirmed: {auction_id}")
