import asyncio
import aiohttp
import json
import logging
import sys

from time import perf_counter, sleep

from generate_ssp_user import generate_ssp_user

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

async def make_ad_request(client: aiohttp.ClientSession, idx: int):
    async with client.post(
            f'http://localhost:8000/ad_request',
            json=generate_ssp_user(idx=idx)
        ) as response:
        response_body = await response.text()
        if response.status != 200:
            logger.debug(f"response: {response_body}")
        return {
                'status': response.status,
                'body': response_body,
                'idx': idx
                }

async def fetch_all(client, urls): 
    tasks = [make_ad_request(client, url) for url in urls]
    result = await asyncio.gather(*tasks)
    return result

async def main(request_num: int):
    urls = range(0, request_num)
    while True:
        async with aiohttp.ClientSession() as client:
            htmls = await fetch_all(client, urls)
        sleep(5)

if __name__ == '__main__':
    request_num = int(sys.argv[1])
    start = perf_counter()
    asyncio.run(main(request_num))
    logger.debug(f"{request_num} requests elapsed in {(perf_counter() - start) *1000}ms.")


