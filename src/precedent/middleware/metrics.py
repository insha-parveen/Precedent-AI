"""Prometheus metrics middleware for Precedent API.

Collects and exposes metrics for monitoring and alerting.
"""
from __future__ import annotations

import time
from typing import Callable

from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
from starlette.types import ASGIApp

from src.precedent.config import settings


# Define metrics
REQUEST_COUNT = Counter(
    'precedent_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'http_status']
)

REQUEST_LATENCY = Histogram(
    'precedent_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'precedent_http_requests_active',
    'Number of active HTTP requests'
)

# Business metrics
QUERY_COUNT = Counter(
    'precedent_queries_total',
    'Total contract queries processed',
    ['skill_used', 'grounded']
)

QUERY_LATENCY = Histogram(
    'precedent_query_duration_seconds',
    'Contract query processing duration in seconds',
    ['skill_used']
)

TOKEN_USAGE = Counter(
    'precedent_token_usage_total',
    'Total token usage',
    ['type', 'model']  # type: input or output
)

ERROR_COUNT = Counter(
    'precedent_errors_total',
    'Total errors',
    ['type', 'endpoint']
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting Prometheus metrics."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only collect metrics for non-metrics endpoints to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        endpoint = request.url.path

        # Increment active requests
        ACTIVE_REQUESTS.inc()

        start_time = time.time()

        try:
            response = await call_next(request)

            # Record metrics
            process_time = time.time() - start_time
            http_status = response.status_code

            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                http_status=http_status
            ).inc()

            REQUEST_LATENCY.labels(
                method=method,
                endpoint=endpoint
            ).observe(process_time)

            return response

        except Exception as exc:
            # Record error metrics
            ERROR_COUNT.labels(
                type=type(exc).__name__,
                endpoint=endpoint
            ).inc()

            # Re-raise the exception
            raise

        finally:
            # Decrement active requests
            ACTIVE_REQUESTS.dec()


def metrics_endpoint() -> StarletteResponse:
    """Endpoint to expose Prometheus metrics."""
    data = generate_latest()
    return StarletteResponse(
        content=data,
        media_type=CONTENT_TYPE_LATEST
    )