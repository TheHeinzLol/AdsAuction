from time import perf_counter
import asyncio
import httpx
import logging 

# initiate logger
logging.basicConfig(
        format='%(levelname)s: %(message)s', 
        encoding='utf-8', 
        level=logging.WARNING
)

logger = logging.getLogger('SimpleLogger')
logger.setLevel(logging.DEBUG)

async def fetch(client: httpx.AsyncClient, idx: int):
    response = await client.get(f'http://localhost:8000/SSP/{idx}')
#    print(f"id: {idx}, status: {response.status_code}")

async def fetch_all(client: httpx.AsyncClient, urls: list[int]):
    tasks = []
    for url in urls:
        task = asyncio.create_task(fetch(client, url))
        tasks.append(task)
    response = await asyncio.gather(*tasks)
    return response

async def main():
    urls = range(1, 500)
    start = perf_counter()
    async with httpx.AsyncClient(trust_env=False) as client:
        await fetch_all(client, urls)
    end = perf_counter()
    print(f"Total time: {end-start}")

asyncio.run(main())

