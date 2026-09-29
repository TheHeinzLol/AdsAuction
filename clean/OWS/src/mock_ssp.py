
import uvicorn

from fastapi import Body, FastAPI

app = FastAPI()

@app.post("/ssp_mock")
async def ssp_answer(payload: dict=Body()):

    return {
            "ad_url": "ssp to ows mock ad url",
            "billing_token": "ssp to ows mock billing token"
    }


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
