import asyncio
import aiohttp
import json
import logging
import random
import sys

from time import perf_counter, sleep

from generate_ssp_user import generate_ssp_user

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def worker_ad_request(client: aiohttp.ClientSession,
                            urls: range,
                            billing_queue: asyncio.Queue
                        ) -> None:
    errors = {}
    while True:
        start = perf_counter()
        htmls = await fetch_all(client, urls, errors, billing_queue)
        logger.debug(f"Got responses: {htmls}")
        logger.info(f"{request_num} requests elapsed in {(perf_counter() - start) *1000}ms.")
        logger.info(f"status codes: {errors}")
        errors = {}
        await asyncio.sleep(3)

async def fetch_all(client: aiohttp.ClientSession,
                    urls: range,
                    errors: dict,
                    billing_queue: asyncio.Queue
                ) -> list[dict]: 
    tasks = [make_ad_request(client, url, errors, billing_queue) for url in urls]
    result = await asyncio.gather(*tasks)
    return result

async def make_ad_request(client: aiohttp.ClientSession,
                          idx: int,
                          errors: dict,
                          billing_queue: asyncio.Queue
                        ) -> dict:
    async with client.post(
            f'http://localhost:8000/ad_request',
            json=generate_ssp_user(idx=idx)
        ) as response:
        response_body = await response.text()
        errors[response.status] = errors.get(response.status, 0) + 1
        if response.status != 200:
            logger.debug(f"Failed to make ad request.\nStatus:{response.status} Got response:\n {response_body}")
        else: 
            response_json = await response.json()
            await billing_queue.put(response_json['confirm_url'])
        return {
                'status': response.status,
                'body': response_body,
                'idx': idx
                }

async def worker_billing(
        client: aiohttp.ClientSession,
        billing_queue: asyncio.Queue
    ) -> None:
    while True:
        billing_id = await billing_queue.get()
        try:
            await confirm_billing(client, billing_id)
        except Exception as e:
            logger.info(f"Failed to confirm billing. Error:\n{e}")
        finally:
            billing_queue.task_done()

async def confirm_billing(
            client: aiohttp.ClientSession,
            billing_id: str
        ) -> None:
    async with client.post(
                'http://localhost:8000/billing_trigger',
                json={"billing_id": billing_id},
            ) as response:
        response_body = await response.text()
        if response.status != 200:
            logger.info(f"Failed to confirm billing. Response:\n{response_body}")
        else:
            logger.info(f"confirmed: {response_body}")

async def main(request_num: int):
    billing_queue = asyncio.Queue()
    urls = range(0, request_num)
    async with (
        aiohttp.ClientSession() as client_ad_request,
        aiohttp.ClientSession() as client_billing,
    ):
        await asyncio.gather(
            worker_ad_request(client_ad_request, urls, billing_queue),
            worker_billing(client_billing, billing_queue)
            )



if __name__ == '__main__':
    request_num = int(sys.argv[1])
    asyncio.run(main(request_num))
