import asyncio
import time
from time import perf_counter
from urllib.parse import urljoin

import aiohttp

ADX_URL = "http://localhost:8002/"
#adx_urls = [urljoin(ADX_URL, "/test") for adx_id in range(1)]
adx_urls = [urljoin(ADX_URL, f"ad_request_adx_{adx_id}") for adx_id in range(1)]
PAYLOAD = {
    "user_id": "user_12345",
    "category": "technology",
    "floor_price": 0.50,
    "device": "mobile",
    "channel": "web",
    "ad_size": [300, 250],
    "region": "DE",
    "languages": ["de", "en"],
    "local_hour": 14,
    "auction_id_ssp": "ssp_auction_98765"
}


async def send_ad_request(session: aiohttp.ClientSession, url: str, payload: dict):
    start = time.perf_counter()
    async with session.post(url=url, json=payload) as response:
        await response.read()  # Ensure the full body is received
        elapsed = time.perf_counter() - start
        return elapsed

async def benchmark(concurrency: int = 50, total_requests: int = 2500):

    api_keys = {}
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8002/fetch_api_keys") as response:
            keys = await response.json()
    for url in adx_urls:
        api_keys[url] = get_api_key(keys, url)

    connector = aiohttp.TCPConnector(enable_cleanup_closed=True)
    async with aiohttp.ClientSession() as session:
        
        semaphore = asyncio.Semaphore(concurrency)
        async def controlled_request(url):
            async with semaphore:
                return await send_ad_request(session, url, PAYLOAD, api_keys[url])
        
        start = time.perf_counter()
        tasks = [controlled_request(url) for url in adx_urls for _ in range(total_requests)]
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start
    
    results.sort()
    p50 = results[int(0.50 * len(results))]
    p95 = results[int(0.95 * len(results))]
    p99 = results[int(0.99 * len(results))]
    
    print(f"Total requests: {total_requests}")
    print(f"Concurrency: {concurrency}")
    print(f"Total time: {elapsed:.2f}s")
    print(f"Throughput: {total_requests / elapsed:.0f} req/sec")
    print(f"Min latency: {min(results)*1000:.2f}ms")
    print(f"p50 latency: {p50*1000:.2f}ms")
    print(f"p95 latency: {p95*1000:.2f}ms")
    print(f"p99 latency: {p99*1000:.2f}ms")
    print(f"Max latency: {max(results)*1000:.2f}ms")


def get_api_key(keys: dict, adx_url: str):
#    return "ass"
    api_keys = keys
    adx_id = adx_url[-1]
    #adx_id = adx_url.split("/")[-1].split("_")[1]
    for key, key_data in api_keys.items():
        if key_data["adx_id"] == adx_id:
            return key
    return "NO KEY"

async def send_ad_request(session, url, payload, api_key):
    start = perf_counter()
    async with session.post(url=url):#, headers={"X-API-KEY": api_key}, json=payload) as response:
#        await response.read()
        return perf_counter()-start

asyncio.run(benchmark(concurrency=50, total_requests=2500))

