
from fastapi import FastAPI
from random import uniform

app = FastAPI(title='DSP FastAPI')

@app.get('/')
def get_root():
    return {'ass':'twat'}

@app.get('/healthz')
def health_check():
    return {"status": "healty"}

@app.post('/bid_request')
async def send_bid():
    return {
            "bidder": "bidder_id",
            "bid_amount": round(uniform(0.5,100), 2),
            "creative_url": "DSP_mock_creative_url"
            }
    
