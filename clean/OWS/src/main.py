import asyncio
import logging
import os
import signal
import sys

from shared.instrument_otel import init_tracing
from shared.metrics_server import start_metrics_server

from .user_pool import populate_user_pool
from .worker_render import worker_render
from .worker_workload import worker_workload

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s [%(funcName)s]:\n%(message)s",
)
logging.getLogger("OWS.src.worker_workload").setLevel(logging.WARNING)
logging.getLogger("OWS.src.generator_request").setLevel(logging.WARNING)
logging.getLogger("OWS.src.worker_render").setLevel(logging.WARNING)
logging.getLogger("OWS.src.delayed_queue").setLevel(logging.WARNING)

METRICS_PORT = int(os.getenv("METRICS_PORT", "8041"))

# Read from environment, fall back to localhost.
# This allows me to edit the script without launching docker compose every time
SSP_URL = os.getenv("SSP_URL", "http://localhost:8001")


async def main(
    requests_per_second: int,
    metrics_server_port: int = METRICS_PORT,
    ssp_url: str = SSP_URL,
):
    # OTel tracing
    init_tracing(service_name="OWS")
    # starting a metrics server for prometheus to scrape
    prometheus_server, thread = start_metrics_server(metrics_server_port)
    # create user pool
    populate_user_pool(10000)
    # Graceful stop set up
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    # declare tasks
    tasks = [
        asyncio.create_task(
            worker_workload(
                ssp_url, requests_per_second=requests_per_second, stop=stop
            ),
            name="workload_task",
        ),
        asyncio.create_task(worker_render(stop), name="render_task"),
    ]
    # wait for graceful stop
    await stop.wait()
    # cancel workers
    for task in tasks:
        task.cancel()

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for task, result in zip(tasks, results):
        if isinstance(result, asyncio.CancelledError):
            logger.info(f"Task {task.get_name()} cancelled")
        elif isinstance(result, Exception):
            logger.error(f"Task {task.get_name()} crashed:\n{result}", exc_info=result)
        else:
            logger.info(f"Task {task.get_name()} stopped cleanly.")

    try:
        prometheus_server.shutdown()
        prometheus_server.server_close()
        thread.join(timeout=2)
        logger.info("Prometheus metrics server shutdown success.")
    except Exception as e:
        logger.error(f"Failed to shutdown Prometheus metrics server:\n{e!s}")


if __name__ == "__main__":
    num_requests = int(sys.argv[1])
    asyncio.run(main(num_requests))
