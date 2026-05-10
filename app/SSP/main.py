import asyncio
import aiohttp

async def fetch(client, idx: int):
    async with client.get(f'http://localhost:8000/SSP/{idx}') as response:
        return response.status
        
async def fetch_all(client, urls):
    tasks = [fetch(client, url) for url in urls]
    result = await asyncio.gather(*tasks)
    return result

async def main():
    request_num = 2500
    urls = range(0, request_num)
    async with aiohttp.ClientSession() as client:
        htmls = await fetch_all(client, urls)

if __name__ == '__main__':
    asyncio.run(main())

