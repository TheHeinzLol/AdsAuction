from fastapi import FastAPI, Body, HTTPException
from random import random, uniform
import asyncio
import aiohttp
import logging
from fastapi.responses import Response

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s [%(funcName)s]:\n%(message)s",
)

app = FastAPI()
ROLL_COUNTER = 0


@app.post("/accept_roll")
async def roll(payload: dict):
    global ROLL_COUNTER
    if random() < 0.25:
        logger.error("Holy fucking boom 403")
        raise HTTPException(status_code=403, detail="Invalid API key 403")
    elif random() < 0.5:
        try:
            raise Exception(
                "SimulatedErrorAgainSimulatedErrorAgainSimulatedErrorAgainSimulatedErrorAgainSimulatedErrorAgainSimulatedErrorAgain"
            )
        except Exception as e:
            logger.error(f"This is str(e):\n{str(e)}")
            logger.error(f"This is e:\n{e}")
    if random() < 0.5:
        asyncio.sleep(uniform(0.25, 1))
    ROLL_COUNTER += 1
    rolled = payload["rolled"]
    return {"got roll": rolled, "ass": "twat"}
