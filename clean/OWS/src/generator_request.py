import logging
from random import choice, random
from time import perf_counter

import aiohttp
from pydantic import ValidationError

from shared.pydantic_models import AdRequestOWS

from .delayed_queue import schedule
from .metrics import AD_REQUEST_DURATION, AD_REQUESTS_SENT, RENDERS_SKIPPED
from .publisher_data import PUBLISHERS
from .user_pool import User, populate_user_pool, user_exhaust_check, pick
from .user_pool import _user_pool as user_pool

logger = logging.getLogger(__name__)
from aiohttp.client_exceptions import ContentTypeError
async def make_ad_request(session: aiohttp.ClientSession, url: str) -> dict:
    before_request = perf_counter()
    user, request_data = generate_request_data()
    request_data = request_data.model_dump()
    #timeout_seconds = 5
    try:
        async with session.post(
            url=url,
            json=request_data,
            #timeout=aiohttp.ClientTimeout(total=timeout_seconds),
        ) as response:
            response_time = (perf_counter() - before_request)
            if response.status not in [200, 204]:
                response_text = await response.text()
                logger.info(
                        f"Ad request did not return 200:\ngot status: {response.status}\nbody:\n{response_text}\nURL: {url}"
                )
                AD_REQUESTS_SENT.labels(status="error").inc()
                AD_REQUEST_DURATION.labels(status="error").observe(response_time)
            else:
                AD_REQUESTS_SENT.labels(status="success").inc()
                AD_REQUEST_DURATION.labels(status="success").observe(response_time)
                if response.status == 204:
                    pass
                else:
                    response_json = await response.json()
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

            user.increment_request_counter()
            user_exhaust_check(user)
            return response_time

    except ContentTypeError as e:
        response_txt = await response.text()
        logger.error(f"conetnt type: {response.headers.get("Content-Type")}\nText:\n{response_txt}")
    except Exception as e:
        logger.error(f"ad request failed. error:\n{str(e)}\nerror_type: {type(e).__name__}\nURL: {url}")
        return {"error": str(e), "error_type": type(e).__name__}


def generate_request_data(debug_mode: bool = False) -> tuple[User, AdRequestOWS]:
    if debug_mode:
        populate_user_pool(1)
    # get user from user_pool
    user = pick()
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
