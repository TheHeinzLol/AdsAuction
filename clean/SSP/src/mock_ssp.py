
from fastapi import Body, FastAPI
from pydantic import BaseModel


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
    #TODO add no bid option
    return {
            "ad_url": "ssp to ows mock ad url",
            "billing_token": "ssp to ows mock billing token"
    }

@app.get("/healthz")
async def healthz():
    return {"status": "healthy"}
