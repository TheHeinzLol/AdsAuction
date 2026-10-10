
import logging
from prometheus_client import start_http_server

logger = logging.getLogger(__name__)

def start_metrics_server(port: int = 8000) -> None:
    start_http_server(port)
    logger.info(
            f"Metrics server started on port {port}",
            f"Metrics available at http://localhost:{port}/metrics"
    )
