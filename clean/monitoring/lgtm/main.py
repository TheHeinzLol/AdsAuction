from fastapi import FastAPI, HTTPException
from random import randint, random
import aiohttp
import logging
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s [%(funcName)s]:\n%(message)s",
)

request_url = "http://fastapi_2:8000/accept_roll"

app = FastAPI()

# --- Prometheus Metrics Definitions ---
ROLL_TOTAL = Counter("app_rolls_total", "Total number of dice rolls")
ROLL_VALUE_TOTAL = Counter(
    "app_roll_value_total", "Count of each specific roll value", ["value"]
)
ROLL_HISTOGRAM = Histogram(
    "app_roll_value_histogram", "Histogram of roll values", buckets=[1, 2, 3, 4, 5, 6]
)


@app.get("/metrics")
async def metrics():
    """Endpoint for Grafana Alloy to scrape"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
async def roll():
    logger.warning("This can end bad")

    if random() < 0.25:
        logger.error("Holy fucking boom 401")
        raise HTTPException(status_code=401, detail="Invalid API key")
    elif random() < 0.5:
        try:
            raise Exception("SimulatedError")
        except Exception as e:
            logger.error(f"This is str(e):\n{str(e)}")
            logger.error(f"This is e:\n{e}")

    # 1. Increment total roll counter
    ROLL_TOTAL.inc()
    status_request = "OK"
    logger.debug("Rolling...")
    roll_value = randint(1, 6)
    logger.info(f"Rolled {roll_value}")

    # 2. Increment counter for the specific value
    ROLL_VALUE_TOTAL.labels(value=str(roll_value)).inc()

    # 3. Observe the value in the histogram
    ROLL_HISTOGRAM.observe(roll_value)
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=request_url,
            json={"rolled": roll_value},
        ) as response:
            if response.status != 200:
                response_text = await response.text()
                logger.warning(f"Request didn't return 200. Got {response.status}")
                logger.debug(f"Response:\n{response_text}")
                status_request = "FAILED"
    return {"request status": status_request, "rolled": roll_value}
