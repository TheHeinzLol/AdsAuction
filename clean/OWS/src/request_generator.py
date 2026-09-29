import aiohttp
import asyncio
import logging
import sys

from time import perf_counter

from .user_generator import generate_user

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def main(num_requests):
    async with aiohttp.ClientSession() as session:
        result = await generate_requests_batch(session, num_requests)
    print(result)

async def generate_requests_batch(
        session: aiohttp.ClientSession,
        num_requests: int
) -> list[dict]:
    url = "http://ssp:8000/ssp_mock"
    connector = aiohttp.TCPConnector(limit=400)
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            batch_start = perf_counter()
            responses = await fetch_all(session, url, num_requests)
            elapsed = perf_counter() - batch_start
            if elapsed < 1:
                logger.debug(f"Batch elaplsed in {elapsed}s.")
                await asyncio.sleep(1 - elapsed)
            else:
                logger.warning(
                        f"Batch elapsed in {elapsed}s, exceeding target."
                        f"Can't keep up with {num_requests} req/s"
                        )
    return responses

async def fetch_all(
        session: aiohttp.ClientSession,
        url: str,
        num_requests: int = 1
) -> list[dict]:
    tasks = [make_ad_request(session, url) for i in range(num_requests)]
    try:
        responses = await asyncio.gather(*tasks)
    except Exception as e:
        logger.error(f"Failed to gather ad requests result:\n{e}")
    return responses
   
async def make_ad_request(
        session: aiohttp.ClientSession,
        url: str
) -> dict: 
    try:
        async with session.post(
                    url=url,
                    json=generate_user()
                    ) as response:
            resp = await response.json()
            if response.status != 200:
                logger.info(f"Ad request not 200:\nGot status: {response.status}\nBody:\n{resp}")      
            return resp
    except Exception as e:
        logger.error(f"Ad request failed. Error:\n{e}")
        return {"error": e}
 

if __name__ == "__main__":
    num_requests = int(sys.argv[1])
    asyncio.run(main(num_requests))

