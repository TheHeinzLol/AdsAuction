import time
from fastapi import Request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Awaitable


REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests received",
    labelnames=["endpoint", "method", "status"]
)

REQUESTS_DURATION = Histogram(
    "ad_request_duration_seconds",
    "HTTP request duration in seconds",
    labelnames=["endpoint", "method"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1)
)

REQUESTS_BY_DEVICE = Counter(
    "ad_requests_by_device",
    "Requests segmented by device type",
    labelnames=["device"]  
)

REQUESTS_BY_REGION = Counter(
    "ad_requests_by_region",
    "Requests by geographic region",
    labelnames=["region"] 
)
class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Production-grade Prometheus metrics middleware for FastAPI.
    
    Tracks:
    - Request count by endpoint, method, and status code
    - Request duration in seconds
    """
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """
        Process each request, record metrics, and return response.
        """
        # Start timer
        start_time = time.perf_counter()
        # Process the request
        response = await call_next(request)
        # Calculate duration in seconds
        duration = time.perf_counter() - start_time
        endpoint = request.url.path
        # Record metrics
        REQUESTS_TOTAL.labels(
            endpoint=endpoint,
            method=request.method,
            status=str(response.status_code)
        ).inc()
        
        REQUESTS_DURATION.labels(
            endpoint=endpoint,
            method=request.method
        ).observe(duration)
        
        return response

async def metrics_endpoint():
    """
    Exposes Prometheus metrics at /metrics endpoint.
    """
    return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
)

def setup_prometheus(app):
    """
    Convenience function to add Prometheus monitoring to a FastAPI app.
    
    Usage:
        from app.exchange.middleware.metrics import setup_prometheus
        setup_prometheus(app)
    """
    # Add middleware
    app.add_middleware(PrometheusMiddleware)
    # Add metrics endpoint
    app.add_api_route("/metrics", metrics_endpoint, methods=["GET"])


