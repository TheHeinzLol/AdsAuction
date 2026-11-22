import asyncio
import logging
import sys
from time import perf_counter
from urllib.parse import urljoin

import aiohttp

from .generator_request import make_ad_request

logger = logging.getLogger(__name__)

async def worker_workload(url: str, requests_per_second: int, stop: asyncio.Event, concurrency: int):
    """Set up client session and run workload generator forever"""
    connector = aiohttp.TCPConnector(limit=concurrency, enable_cleanup_closed=True) # Match your batch size
    url = urljoin(url, "/ad_request")
    async with aiohttp.ClientSession(connector=connector) as session:
        logger.debug("Starting generate_workload")
        await generate_workload(session, url, requests_per_second, stop, concurrency)


async def generate_workload(
    session: aiohttp.ClientSession,
    url: str,
    requests_per_second: int,
    stop: asyncio.Event,
    concurrency: int
):
    """Run batches of requests every second until stopped"""
    while not stop.is_set():
        batch_start = perf_counter()

        responses = await generate_request_batch(session, url, concurrency, requests_per_second)
        elapsed = perf_counter() - batch_start
        if elapsed < 1:
            logger.info(f"Batch: {len(responses)} responses in {elapsed}s")
            try:
                await asyncio.wait_for(stop.wait(), timeout=1 - elapsed)
            except TimeoutError:
                pass  # Normal: timeout means no stop signal so we move on
        else:
            logger.info(
                f"Batch of {len(responses)} elapsed in {elapsed}s, exceeding target."
                f"Can't keep up with {requests_per_second} req/s"
            )

            responses.sort()
            p50 = responses[int(0.50 * len(responses))]
            p95 = responses[int(0.95 * len(responses))]
            p99 = responses[int(0.99 * len(responses))]
            
            logger.info(f"Concurrency: {concurrency}")
            logger.info(f"Total time: {elapsed:.2f}s")
            logger.info(f"Throughput: {2500 / elapsed:.0f} req/sec")
            logger.info(f"Min latency: {responses[0]*1000:.2f}ms")
            logger.info(f"p50 latency: {p50*1000:.2f}ms")
            logger.info(f"p95 latency: {p95*1000:.2f}ms")
            logger.info(f"p99 latency: {p99*1000:.2f}ms")
            logger.info(f"Max latency: {responses[-1]*1000:.2f}ms")

        break
    logger.info("Workload generator exited while loop due to stop signal")


async def generate_request_batch(
        session: aiohttp.ClientSession, url: str, concurrency: int, num_requests: int = 1
) -> list[dict]:
    semaphore = asyncio.Semaphore(concurrency)
    async def controlled_request():
        async with semaphore:
            return await make_ad_request(session, url)
    responses = []  # in case nothing will be gathered
    tasks = [controlled_request() for i in range(num_requests)]
    try:
        responses = await asyncio.gather(*tasks)
    except Exception as e:
        logger.error(f"Failed to gather ad requests result:\n{e}")
    return responses


if __name__ == "__main__":
    num_requests = int(sys.argv[1])
    asyncio.run(worker_workload(num_requests))
