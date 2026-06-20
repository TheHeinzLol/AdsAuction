import secrets
import os

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI
from random import uniform

dsp_list = [f'dsp_{i}' for i in range(3)]
VALID_KEYS = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    #generating api keys
    for dsp in dsp_list:
        VALID_KEYS[dsp] = {
                'key': secrets.token_urlsafe(16),
                'created_at': datetime.now(timezone.utc).isoformat(),
                }
    yield
    
app = FastAPI(title='DSP FastAPI', lifespan=lifespan)


@app.get('/')
def get_root():
    return {'ass':'twat'}

@app.get('/healthz')
def health_check():
    return {"status": "healty"}

@app.get('/get_api_keys')
def get_api_keys():
    return VALID_KEYS

@app.post('/bid_request')
async def send_bid():
    #check api keys
    return {
            "bidder": "bidder_id",
            "bid_amount": round(uniform(0.5,100), 2),
            "creative_url": "DSP_mock_creative_url"
            }

# secreta

