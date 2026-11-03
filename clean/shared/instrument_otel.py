import logging
import socket
from urllib.parse import urlparse
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor

_initialized = False

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s [%(funcName)s]:\n%(message)s",
)


def init_tracing(service_name: str, alloy_endpoint: str = "http://alloy_rtb:4317"):
    """Initialize OpenTelemetry tracing."""
    global _initialized
    parsed_url = urlparse(alloy_endpoint)

    # pass if already initialized or can't reach alloy
    if _initialized:
        logger.info(f"OTel tracing is already initialized by {service_name} service.")
        return
    elif not is_endpoint_reachable(parsed_url.hostname, parsed_url.port):
        logger.info(
            f"Alloy endpoint is not reachable by {service_name}. Skipping tracing init."
        )
        return

    # 1. Set up the tracer provider
    provider = TracerProvider()
    trace.set_tracer_provider(provider)

    # 2. Configure the exporter to send to Alloy
    exporter = OTLPSpanExporter(endpoint=alloy_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))

    # 3. Instrument aiohttp
    AioHttpClientInstrumentor().instrument()

    _initialized = True
    logger.info(f"OTel tracing is initialized by {service_name} service.")
    return


def is_endpoint_reachable(host: str, port: int, timeout: float = 2.0) -> bool:
    """Check if a TCP port is open and accepting connections."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False
