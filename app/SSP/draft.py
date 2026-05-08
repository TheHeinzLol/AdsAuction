from time import perf_counter
import asyncio
import httpx

async def fetch(client: httpx.AsyncClient, idx: int):
    response = await client.get(f'http://localhost:8000/SSP/{idx}')
    return idx  # return something to measure success

async def main():
    urls = list(range(1, 500))
    
    async with httpx.AsyncClient(
        trust_env=False,
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
    ) as client:
        start = perf_counter()
        results = await asyncio.gather(*[fetch(client, url) for url in urls])
        end = perf_counter()
        
        elapsed = end - start
        req_per_sec = len(urls) / elapsed
        print(f"500 requests: {elapsed:.2f}s")
        print(f"Throughput: {req_per_sec:.0f} req/sec")
        print(f"Avg latency: {elapsed/len(urls)*1000:.1f} ms/req")

asyncio.run(main())
