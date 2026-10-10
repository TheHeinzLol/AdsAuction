import aiohttp
import asyncio
import logging
import signal
import sys

from .generator_request import worker_workload
from .metrics_server import start_metrics_server
from .worker_render import worker_render


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.getLogger("OWS.src.generate_request").setLevel(logging.INFO)
logging.getLogger("OWS.src.worker_render").setLevel(logging.WARNING)
logging.getLogger("OWS.src.delayed_queue").setLevel(logging.WARNING)


async def main(requests_per_second: int):
    #TODO should I check if server is stopped with cancellation and notify of it?
    start_metrics_server(8043)#TODO this port is hardcoded. Replace with env var
    # Graceful stop set up
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    # declare tasks
    tasks = [
        asyncio.create_task(
            worker_workload(requests_per_second=requests_per_second, stop=stop),
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


if __name__ == "__main__":
    num_requests = int(sys.argv[1])
    asyncio.run(main(num_requests))
