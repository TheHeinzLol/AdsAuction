import logging

from prometheus_client import start_http_server

logger = logging.getLogger(__name__)


def start_metrics_server(port: int = 8041) -> None:
    server, thread = start_http_server(port)
    logger.info(
        f"Metrics server started on port {port}.\n"
        "If you run the server outside docker container,"
        f"Metrics available at http://localhost:{port}/metrics",
    )
    return (server, thread)
