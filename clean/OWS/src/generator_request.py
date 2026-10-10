import aiohttp
import asyncio
import logging
import os
import signal
import sys
from time import perf_counter
from random import random
from urllib.parse import urljoin

from .delayed_queue import schedule
from .generator_user import generate_user
from .metrics import AD_REQUESTS_SENT, RENDERS_SKIPPED

logger = logging.getLogger(__name__)
# Read from environment, fall back to localhost.
# This allows me to edit the script without launching docker compose every time
SSP_URL = os.getenv("SSP_URL", "http://localhost:8000")


async def worker_workload(requests_per_second: int, stop: asyncio.Event):
    """Set up client session and run workload generator forever"""

    url = urljoin(SSP_URL, "/ssp_mock")
    async with aiohttp.ClientSession() as session:
        logger.debug("Starting generate_workload")
        await generate_workload(session, url, requests_per_second, stop)


async def generate_workload(
    session: aiohttp.ClientSession,
    url: str,
    requests_per_second: int,
    stop: asyncio.Event,
):
    """Run batches of requests every second until stopped"""
    while not stop.is_set():
        batch_start = perf_counter()

        responses = await generate_request_batch(session, url, requests_per_second)

        elapsed = perf_counter() - batch_start
        if elapsed < 1:
            logger.debug(f"Batch: {len(responses)} responses in {elapsed}s")
            try:
                await asyncio.wait_for(stop.wait(), timeout=1 - elapsed)
            except asyncio.TimeoutError:
                pass  # Normal: timeout means no stop signal so we move on
        else:
            logger.info(
                f"Batch elapsed in {elapsed}s, exceeding target."
                f"Can't keep up with {num_requests} req/s"
            )
    logger.info("Workload generator exited while loop due to stop signal")


async def generate_request_batch(
    session: aiohttp.ClientSession, url: str, num_requests: int = 1
) -> list[dict]:
    responses = []  # in case nothing will be gathered
    tasks = [make_ad_request(session, url) for i in range(num_requests)]
    try:
        responses = await asyncio.gather(*tasks)
    except Exception as e:
        logger.error(f"Failed to gather ad requests result:\n{e}")
    return responses


async def make_ad_request(session: aiohttp.ClientSession, url: str) -> dict:
    try:
        async with session.post(url=url, json=generate_user()) as response:
            resp = await response.json()
            if response.status != 200:
                logger.info(
                    f"ad request not 200:\ngot status: {response.status}\nbody:\n{resp}"
                )
                AD_REQUESTS_SENT.labels(status="error").inc()
            else:
                AD_REQUESTS_SENT.labels(status="success").inc()
                roll = random()
                # immediate render
                if roll < 0.85:
                    logger.debug(f"Scheduling {resp['auction_id']}")
                    schedule(ttl=0, auction_id=resp["auction_id"])
                # expire
                elif roll < 0.95:
                    logger.debug(f"Scheduling {resp['auction_id']}")
                    schedule(ttl=resp["ttl"], auction_id=resp["auction_id"])
                # 5% chance to skip rendering entirely: adblock or page abandon etc.
                else:
                    RENDERS_SKIPPED.inc()
                    logger.debug(f"Not scheduling {resp['auction_id']}")
            return resp
    except Exception as e:
        logger.error(f"ad request failed. error:\n{e}")
        return {"error": str(e), "error_type": type(e).__name__}


if __name__ == "__main__":
    num_requests = int(sys.argv[1])
    asyncio.run(worker_workload(num_requests))
