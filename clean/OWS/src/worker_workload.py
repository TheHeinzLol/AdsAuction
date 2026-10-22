import asyncio
import logging
import os
import sys
from time import perf_counter
from urllib.parse import urljoin

import aiohttp

from .generator_request import make_ad_request

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s [%(funcName)s]:\n%(message)s",
)

# Read from environment, fall back to localhost.
# This allows me to edit the script without launching docker compose every time
SSP_URL = os.getenv("SSP_URL", "http://localhost:8000")


async def worker_workload(requests_per_second: int, stop: asyncio.Event):
    """Set up client session and run workload generator forever"""

    url = urljoin(SSP_URL, "/ad_request")
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
            except TimeoutError:
                pass  # Normal: timeout means no stop signal so we move on
        else:
            logger.info(
                f"Batch elapsed in {elapsed}s, exceeding target."
                f"Can't keep up with {requests_per_second} req/s"
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


if __name__ == "__main__":
    num_requests = int(sys.argv[1])
    asyncio.run(worker_workload(num_requests))
