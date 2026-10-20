import asyncio
import logging
import os
import sys
from random import choice, random
from time import perf_counter
from typing import TypedDict
from urllib.parse import urljoin

import aiohttp

from .delayed_queue import schedule
from .publisher_data import PUBLISHERS
from .user_pool import User, USER_POOL, user_exhaust_check
from .metrics import AD_REQUEST_DURATION, AD_REQUESTS_SENT, RENDERS_SKIPPED

logger = logging.getLogger(__name__)
# Read from environment, fall back to localhost.
# This allows me to edit the script without launching docker compose every time
SSP_URL = os.getenv("SSP_URL", "http://localhost:8000")


class RequestDataProfile(TypedDict):
    user_id: str
    publisher_id: str
    floor_price: float
    device: str
    channel: str
    category: str
    ad_size: tuple[int, int] | None
    region: str
    languages: list[str]
    local_hour: int


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
    before_request = perf_counter()
    user, json = generate_request_data()
    timeout_seconds = 0.1
    try:
        async with session.post(
            url=url, json=json, timeout=aiohttp.ClientTimeout(total=timeout_seconds)
        ) as response:
            response_time = (perf_counter() - before_request) * 1000  # ms instead of s
            if response.status != 200:
                response_text = await response.text()
                logger.info(
                    f"Ad request did not return 200:\ngot status: {response.status}\nbody:\n{response_text}"
                )
                AD_REQUESTS_SENT.labels(status="error").inc()
                AD_REQUEST_DURATION.labels(status="error").observe(response_time)
                return response_text
            else:
                response_json = await response.json()
                AD_REQUESTS_SENT.labels(status="success").inc()
                AD_REQUEST_DURATION.labels(status="success").observe(response_time)
                roll = random()
                # immediate render
                if roll < 0.85:
                    logger.debug(f"Scheduling {response_json['auction_id_ssp']}")
                    schedule(ttl=0, auction_id=response_json["auction_id_ssp"])
                # expire
                elif roll < 0.95:
                    logger.debug(f"Scheduling {response_json['auction_id_ssp']}")
                    schedule(
                        ttl=response_json["ttl"],
                        auction_id=response_json["auction_id_ssp"],
                    )
                # 5% chance to skip rendering entirely: adblock or page abandon etc.
                else:
                    RENDERS_SKIPPED.inc()
                    logger.debug(f"Not scheduling {response_json['auction_id_ssp']}")
            # manage user
            user.increment_request_counter()
            user_exhaust_check(user)
            return response_json
    except Exception as e:
        logger.error(f"ad request failed. error:\n{e}")
        return {"error": str(e), "error_type": type(e).__name__}


def generate_request_data() -> tuple[User, RequestDataProfile]:
    # get user from user_pool
    user = choice(USER_POOL)
    # decide if publisher will match user's preference or will be chosen randomly
    if random() > 0.33:
        publishers = [
            publisher
            for publisher in PUBLISHERS
            if publisher["category"] == user.data["preference"]
        ]
    else:
        publishers = PUBLISHERS
    # get a publisher
    publisher = choice(publishers)
    request_data = {**user.data, **publisher}
    del request_data["preference"]
    # return user
    return user, request_data


if __name__ == "__main__":
    num_requests = int(sys.argv[1])
    asyncio.run(worker_workload(num_requests))
