import asyncio
import time

import aiohttp

URL = "http://localhost:8001/ad_request"
ad_request_ows = {
    "user_id": "user_12345",
    "category": "technology",
    "floor_price": 0.50,
    "device": "mobile",
    "channel": "web",
    "ad_size": [300, 250],
    "region": "DE",
    "languages": ["de", "en"],
    "local_hour": 14,
    "publisher_id": "publisher_001",
}

async def send_ad_request(session: aiohttp.ClientSession, url: str, payload: dict):
    start = time.perf_counter()
    async with session.post(url=url, json=payload) as response:
        await response.read()  # Ensure the full body is received
        elapsed = time.perf_counter() - start
        return elapsed

async def benchmark(concurrency: int = 50, total_requests: int = 2500):
    connector = aiohttp.TCPConnector(enable_cleanup_closed=True) #limit=concurrency is redundant
    async with aiohttp.ClientSession() as session:
        
        semaphore = asyncio.Semaphore(concurrency)
        async def controlled_request():
            async with semaphore:
                return await send_ad_request(session, URL, ad_request_ows)
        
        start = time.perf_counter()
        tasks = [controlled_request() for _ in range(total_requests)]
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

asyncio.run(benchmark(concurrency=50, total_requests=500))

