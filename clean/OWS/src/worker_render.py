import aiohttp
import asyncio
import logging
import os
import time
from urllib.parse import urljoin

from .delayed_queue import peek, pop, size
from .metrics import RENDERS_CONFIRMED

logger = logging.getLogger(__name__)

SSP_URL = os.getenv("SSP_URL", "http://localhost:8000")
render_url = urljoin(SSP_URL, "/confirm_render")


async def worker_render(stop: asyncio.Event):
    connector = aiohttp.TCPConnector(limit=400)
    async with aiohttp.ClientSession(connector=connector) as session:
        await render_ad(session, stop)


async def render_ad(session: aiohttp.ClientSession, stop: asyncio.Event):
    """
    Perpetually checks for items in queue to send render confirmation.
    Waits 0.1s if queue is empty.
    """
    while not stop.is_set():
        item = peek()
        if item is None:
            await asyncio.sleep(0.1)
            continue

        send_at, auction_id = item
        now = time.time()
        if send_at <= now:
            logger.debug(f"sending item {item}")
            pop()
            try:
                await send_render_confirmation(
                    session=session, url=render_url, auction_id=auction_id
                )
            except Exception as e:
                logger.info(f"\nFailed render confirmation request. Error:\n{e}\n")
        else:
            await asyncio.sleep(min(send_at - now, 0.1))


async def send_render_confirmation(
    session: aiohttp.ClientSession, url: str, auction_id: str
) -> None:
    async with session.post(
        url=render_url, json={"auction_id": auction_id, "render_status": "rendered"}
    ) as response:
        response_body = await response.json()
        if response.status != 200:
            logger.info(f"\nFailed to confirm rendering. Response:\n{response_body}")
        else:
            RENDERS_CONFIRMED.inc()
            logger.debug(f"\nRender confirmed: {auction_id}")
