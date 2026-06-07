import aiohttp
import asyncio

DSP_ENDPOINTS = [
        {
            "dsp_id": "dsp_1",
            "url": "http://localhost:8001/bid_request",
            "api_key": "key_1"
        }
]
user_info = {'local_hour': 8, 'region': 'JPN', 'languages': ['English', 'Japanese'], 'device': 'billboard', 'channel': 'billboard display', 'categories': ['health', 'pets', 'beauty', 'fashion', 'finance', 'food'], 'ad_size': [1920, 1080]}
async def send_bid_request(url, user_info):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=user_info) as response:
            response_body = await response.text()
            print(response_body)
            return response_body

if __name__ == '__main__':
    asyncio.run(send_bid_request(DSP_ENDPOINTS[0]['url'], user_info))

