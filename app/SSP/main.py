import asyncio
import aiohttp
import random

from datetime import datetime, timedelta, timezone
from pycountry import countries
from typing import Dict


async def generate_ssp_user_info() -> Dict:
    tz = timezone(timedelta(hours=random.randint(-12, 12)))
    date = datetime.now(tz)

    region = random.choice(pycountry.countries).alpha_2

    devices = ["pc", "phone", "display"]
    device = random.choices(devices, weights=[0.4, 0.4, 0.2], k=1)

    channels = ["social", "search", "streaming_video", "streaming_audio"]
    channel = random.choices(channels, weights=[0.4, 0.4, 0.1, 0.1]) if device is not "display" else "display"

    categories = ["technology", "pets", "beauty", "healthcare", "games", "food", "automobiles"]
    category = random.choice(categories)

    ssp_user_info = {
            'timestamp': date,
            'region': region,
            'device': device,
            'channel': channel,
            'category': category
            }
    return ssp_user_info

async def fetch(client: aiohttp.ClientSession, idx: int):
    async with client.get(f'http://localhost:8000/SSP/{idx}') as response:
        return response.status
        
async def make_ad_request(client: aiohttp.ClientSession, idx: int):
    async with client.post(
            f'http://localhost:8000/SSP/{idx}',
            json=generate_ssp_user_info()
        ) as response:
        return response

async def fetch_all(client, urls): 
    tasks = [make_ad_request(client, url) for url in urls]
    result = await asyncio.gather(*tasks)
    return result

async def main():
    request_num = 2000
    urls = range(0, request_num)
    async with aiohttp.ClientSession() as client:
        htmls = await fetch_all(client, urls)

if __name__ == '__main__':
    asyncio.run(main())

