# benchmark_ssp.py
import asyncio
import aiohttp
import time

SSP_URL = "http://localhost:8001/ad_request"
NUM_REQUESTS = 2500
json = {'user_id': 'f69b84b5', 'device': 'tablet', 'channel': 'social', 'ad_size': (160, 600), 'region': 'USA', 'languages': ['English', 'Spanish'], 'local_hour': 23, 'publisher_id': 'pub_webmd', 'category': 'health', 'floor_price': 1.5}
async def send_request(session):
    async with session.post(SSP_URL, json=json) as resp:
        return resp.status

async def main():
    # Use a high limit and enable cleanup
    connector = aiohttp.TCPConnector(
        limit=500,
        enable_cleanup_closed=True,
    )
    async with aiohttp.ClientSession(connector=connector) as session:
        start = time.perf_counter()
        tasks = [send_request(session) for _ in range(NUM_REQUESTS)]
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start

    print(f"{NUM_REQUESTS} requests in {elapsed:.3f}s")
    print(f"Throughput: {NUM_REQUESTS / elapsed:.0f} req/sec")
    print(f"Statuses: {set(results)}")

if __name__ == "__main__":
    asyncio.run(main())
