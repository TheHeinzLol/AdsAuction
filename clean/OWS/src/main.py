
import aiohttp
import asyncio
import logging
import signal
import sys

from .generator_request import worker_workload
from .worker_render import worker_render


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.getLogger("OWS.src.generate_request").setLevel(logging.WARNING)
logging.getLogger("OWS.src.worker_render").setLevel(logging.WARNING)
logging.getLogger("OWS.src.delayed_queue").setLevel(logging.WARNING)

async def main(requests_per_second: int):
    # Graceful stop set up
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    # start tasks
    tasks = {
            "workload": 
                asyncio.create_task(
                    worker_workload(requests_per_second=requests_per_second, stop=stop),
                    name="workload_task"
                ),
            "render":
                asyncio.create_task(worker_render(stop), name="render_task")
                }
    # wait for graceful stop
    await stop.wait()
    # cancel workers
    for name, task in tasks.items():
        task.cancel()

    results =  await asyncio.gather(
            *tasks.values(),
            return_exceptions=True
    )
    for task, result in zip(tasks.values(), results):
        if isinstance(result, Exception):
            logger.error(f"Task {task.get_name()} crashed:\n{result}", exc_info=result)
        else:
            logger.info(f"Task {task.get_name()} stopped cleanly.")

if __name__ == "__main__":
    num_requests = int(sys.argv[1])
    asyncio.run(main(num_requests))

