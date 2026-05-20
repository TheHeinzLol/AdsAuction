import asyncio
import aiohttp
import logging
import random

from datetime import datetime, timedelta, timezone
from pycountry import countries, languages
from time import perf_counter
from typing import Dict

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)

async def generate_ssp_user_info() -> Dict:
    local_hour = random.randint(0, 23)

    region = random.choice(list(countries)).alpha_3

    language = random.choice(list(languages)).alpha_3

    devices = ["pc", "phone", "display"]
    device = random.choices(devices, weights=[0.4, 0.4, 0.2], k=1)[0]

    channels = ["social", "search", "streaming_video", "streaming_audio"]
    channel = random.choices(channels, weights=[0.4, 0.4, 0.1, 0.1])[0] \
                                if device != "display" else "display"

    categories = ["technology", "pets", "beauty", "healthcare", "games", "food", "automobiles"]
    category = random.choice(categories)

    ssp_user_info = {
            'local_hour': local_hour,
            'region': region,
            'language': language,
            'device': device,
            'channel': channel,
            'category': category
            }
    logger.debug(f"ssp_user_info: {ssp_user_info}")
    return ssp_user_info

async def make_ad_request(client: aiohttp.ClientSession, idx: int):
    async with client.post(
            f'http://localhost:8000/SSP/{idx}',
            json= await generate_ssp_user_info()
        ) as response:
        logger.debug(f"response: {await response.text()}")
        return response

async def fetch_all(client, urls): 
    tasks = [make_ad_request(client, url) for url in urls]
    result = await asyncio.gather(*tasks)
    return result

async def main(request_num: int):
    urls = range(0, request_num)
    async with aiohttp.ClientSession() as client:
        htmls = await fetch_all(client, urls)
    
if __name__ == '__main__':
    request_num = 1
    start = perf_counter()
    asyncio.run(main(request_num))
    logger.debug(f"{request_num} requests elapsed in {(perf_counter() - start) *1000}ms.")
