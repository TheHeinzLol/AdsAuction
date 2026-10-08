
from fastapi import Body, FastAPI
from pydantic import BaseModel
from random import choice #for choosing a ttl
from uuid import uuid4

app = FastAPI()


class AdRequest(BaseModel):
    device: str
    channel: str
    ad_size: list | None
    region: str
    languages: list
    local_hour: int
    categories: list

@app.post("/ssp_mock")
async def ssp_answer(payload: AdRequest) -> dict:
    return {
            "ad_url": "ssp to ows mock ad url",
            "auction_id": str(uuid4())[:8], # to escape dealing with long id for a simple mock
            "ttl": choice([5,10,15])
    }

@app.post("/confirm_render")
async def confirm_render() -> dict:
    return {"render": "accepted"}

@app.get("/healthz")
async def healthz():
    return {"status": "healthy"}
