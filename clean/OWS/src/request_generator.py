import aiohttp
import asyncio

from .user_generator import generate_user

async def generate_request():

    user_data = generate_user()

    async with aiohttp.ClientSession() as session:
       async with session.post(
                url="http://localhost:8000/ssp_mock",
                json=user_data
                ) as response:
            resp = await response.json()
            print(resp)

async def main():
    await generate_request()

if __name__ == "__main__":
    asyncio.run(main())


