
import uvicorn

from fastapi import Body, FastAPI

app = FastAPI()

@app.post("/ssp_mock")
async def ssp_answer(payload: dict=Body()):

    return {"ssp_answer": "ok", "device": payload['device']}


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
