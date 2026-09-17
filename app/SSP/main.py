import asyncio
import aiohttp
import json
import logging
import sys

from time import perf_counter, sleep

from generate_ssp_user import generate_ssp_user

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
# test
errors = {}
# test end
async def make_ad_request(client: aiohttp.ClientSession, idx: int):
    async with client.post(
            f'http://localhost:8000/ad_request',
            json=generate_ssp_user(idx=idx)
        ) as response:
        response_body = await response.text()
        errors[response.status] = errors.get(response.status, 0) + 1
        if response.status != 200:
            logger.debug(f"Failed to make ad request.\nStatus:{response.status} Got response:\n {response_body}")
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
    global errors
    urls = range(0, request_num)
    async with aiohttp.ClientSession() as client:
        while True:
            start = perf_counter()
            htmls = await fetch_all(client, urls)
            logger.debug(f"Got responses: {htmls}")
            logger.info(f"{request_num} requests elapsed in {(perf_counter() - start) *1000}ms.")
            logger.info(f"status codes: {errors}")
            errors = {}
            await asyncio.sleep(3)

if __name__ == '__main__':
    request_num = int(sys.argv[1])
    asyncio.run(main(request_num))
