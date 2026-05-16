import aiohttp
import asyncio
import string
from random import choice, choices

import sys
from pathlib import Path

# Add the project root to Python path so 'app' becomes importable
project_root = Path(__file__).parent.parent.parent.parent  # Goes up to 'AdsAuction/'
sys.path.insert(0, str(project_root))

from app.exchange.schemas.schemas import UserCreateSchema

def generate_login(login_min_length: int, login_max_length: int) -> str:
    """
    Generate a random login of 3-20 length characters,
    including letters of random cases and digits.
    login_min_length: positive integer.
    login_max_length: positive integer.
    """
    length = choice(range(login_min_length, login_max_length+1))
    return ''.join(choices(string.ascii_letters + string.digits, k=length))

def generate_user(login:str) -> dict:
    return {
            'login': login,
            'email': f"{login}@fakemail.com",
            'password': login
            }

async def create_random_user(
        client: aiohttp.ClientSession,
        login_min_length: int,
        login_max_length: int,
        ) -> int:
    login = generate_login(login_min_length, login_max_length)
    user_data = generate_user(login)
    async with client.post(
            f'http://localhost:8000/sign_up',
            json = user_data
            ) as response:
        if response.status != 201:
            print(f"text: {await response.text()}")
            print(f"user data: {user_data}")
        return response.status
        
async def fetch_all(
        client: aiohttp.ClientSession,
        users_num: int,
        login_min_length: int,
        login_max_length: int
        ) -> list[int]:

    tasks = [create_random_user(
                    client,
                    login_min_length,
                    login_max_length
                    )
             for _ in range(users_num)]
    return await asyncio.gather(*tasks)

async def main():
    request_num = 100
    login_min_length = 3
    login_max_length = 20
    async with aiohttp.ClientSession() as client:
        statuses = await fetch_all(client, request_num, login_min_length, login_max_length)
    print(f"Successful: {sum(1 for s in statuses if s == 201)}/{len(statuses)}")

if __name__ == '__main__':
    from time import perf_counter
    start = perf_counter()
    asyncio.run(main())
    print((perf_counter() - start) * 1000)
