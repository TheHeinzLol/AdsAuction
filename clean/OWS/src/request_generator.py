import aiohttp
import asyncio

from .user_generator import generate_user


async def fetch_all(
        session: aiohttp.ClientSession,
        url: str,
        num_requests: int = 1
) -> list[dict]:
    tasks = [make_ad_request(session, url) for i in range(num_requests)]
    result = await asyncio.gather(*tasks)
    return result
   
async def make_ad_request(
        session: aiohttp.ClientSession,
        url: str
) -> dict: #TODO any dict or should I make a typed one?
    async with session.post(
                url=url,
                json=generate_user()
                ) as response:
        resp = await response.json()
        if response.status != 200:
            #TODO logger pring error or log the result
            pass
        return resp
 
async def main():
    url = "http://localhost:8000/ssp_mock"
    async with aiohttp.ClientSession() as session:
        responses = await fetch_all(session, url, 1000)

if __name__ == "__main__":
    asyncio.run(main())

