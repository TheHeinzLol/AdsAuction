import asyncio
import logging
import random
import secrets
import os

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import Body, FastAPI, Header, HTTPException, Request
from random import uniform

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

num_dsp = 5
dsp_list = [f'dsp_{i}' for i in range(num_dsp)]
VALID_KEYS ={}

async def dsp_action(
        request: Request,
        payload: dict = Body(),
        x_api_key: str = Header()
):
    #checks for api keys are separated for testing purposes,
    #but response should not specify if the key is not valid or dsp does not match
    if x_api_key not in VALID_KEYS:
        raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )

    dsp_id = request.url.path.split("/")[-1]

    if VALID_KEYS[x_api_key]['dsp'] != dsp_id:
        raise HTTPException(
                status_code=403,
                detail="API key does not match this DSP"
            )
    answers = [
                {
                "bid_amount": round(uniform(0.5,100), 2),
                "creative_url": "DSP_mock_creative_url"
                },
                {"no":"bids"}
            ]
    # answer is the value we return with 10% chance of returning no bids
    answer = random.choices(answers, weights=[0.9, 0.1], k=1)[0]
    # timeout roughly 1 call out of 10
    if random.random() < 0.1:
        await asyncio.sleep(0.05)
    return {
            "dsp_id": dsp_id,
            "bid_amount": round(uniform(0.5,100), 2),
            "creative_url": f"DSP_mock_creative_url_{dsp_id}",
            "nurl": f"DSP_mock_win_notice_url_{dsp_id}",
            "lurl": f"DSP_mock_loss_notice_url_{dsp_id}",
            "burl": f"DSP_mock_billing_url_{dsp_id}"
            }

@asynccontextmanager
async def lifespan(app: FastAPI):
    #create dsp enpoints
    try:
        for dsp in dsp_list:
            app.add_api_route(f"/{dsp}", dsp_action, methods=["POST"])
            #generating api keys
            VALID_KEYS[secrets.token_urlsafe(16)] = {
                    'dsp': dsp,
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    }
    except Exception as e:
        print(f"Failed to create dsp endpoints: {e}")
    else:
        print("Success: Created dsp endpoints")
        print(f"Valid keys are:\n{VALID_KEYS}")
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
    """This will first choose to return bid or not to,
    and then decide if the responce will take more than 50ms
    =========
    TESTING FUNC DELETE LATER
    ========="""
    # possible responses 
    answers = [
                {
                "bid_amount": round(uniform(0.5,100), 2),
                "creative_url": "DSP_mock_creative_url"
                },
                {"no":"bids"}
            ]
    # answer is the value we return with 10% chance of returning no bids
    answer = random.choices(answers, weights=[0.9, 0.1], k=1)[0]
    # timeout roughly 1 call out of 10
    if random.random() < 0.1:
        await asyncio.sleep(0.05)
    return answer

