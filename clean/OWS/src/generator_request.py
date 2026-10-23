import logging
from random import choice, random
from time import perf_counter

import aiohttp
from pydantic import ValidationError

from shared.pydantic_models import AdRequestOWS

from .delayed_queue import schedule
from .metrics import AD_REQUEST_DURATION, AD_REQUESTS_SENT, RENDERS_SKIPPED
from .publisher_data import PUBLISHERS
from .user_pool import User, user_exhaust_check
from .user_pool import _user_pool as user_pool, populate_user_pool

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s [%(funcName)s]:\n%(message)s",
)


async def make_ad_request(session: aiohttp.ClientSession, url: str) -> dict:
    before_request = perf_counter()
    user, request_data = generate_request_data()
    request_data = request_data.model_dump()
    timeout_seconds = 0.1
    try:
        async with session.post(
            url=url,
            json=request_data,
            timeout=aiohttp.ClientTimeout(total=timeout_seconds),
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
                # 5% chance to skip rendering entirely: adblock, page abandoned, etc.
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


def generate_request_data(debug_mode: bool=False) -> tuple[User, AdRequestOWS]:
    if debug_mode:
        populate_user_pool(1)
    # get user from user_pool
    user = choice(user_pool)
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
    try:
        AdRequestOWS.model_validate(request_data)
        if debug_mode:
            user_pool.clear()
            return AdRequestOWS(**request_data)
        else:
            return user, AdRequestOWS(**request_data)
    except ValidationError as e:
        logger.error(str(e))
