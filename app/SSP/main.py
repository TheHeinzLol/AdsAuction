from time import perf_counter
import asyncio
import httpx
import logging 

# initiate logger
logger = logging.getLogger('SimpleLogger')
logging.basicConfig(format='%(levelname)s: %(message)s', encoding='utf-8', level=logging.DEBUG)

# test fastapi connection
r = httpx.get('http://localhost:8000/SSP/1', trust_env=False)
logger.debug(f"r status: {r.status_code}")
logger.debug(f"r json: {r.json()}")

