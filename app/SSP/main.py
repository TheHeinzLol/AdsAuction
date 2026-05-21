import asyncio
import aiohttp
import logging

from time import perf_counter
from typing import Dict

from generate_ssp_user import generate_ssp_user
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

async def make_ad_request(client: aiohttp.ClientSession, idx: int):
    async with client.post(
            f'http://localhost:8000/SSP/{idx}',
            json= generate_ssp_user()
        ) as response:
        if response.status != 200:
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
    request_num = 100
    start = perf_counter()
    asyncio.run(main(request_num))
    logger.debug(f"{request_num} requests elapsed in {(perf_counter() - start) *1000}ms.")
