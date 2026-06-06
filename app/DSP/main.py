
from fastapi import FastAPI
from random import uniform

app = FastAPI(title='DSP FastAPI')

@app.post('bid_request')
async def send_bid(user_info):
    return {
            "bidder": "bidder_id",
            "bid": uniform(0.5,100),
            "creative_url": "mock_creative_url"
            }
