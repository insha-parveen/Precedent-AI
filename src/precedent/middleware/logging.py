"""Structured logging middleware for Precedent API.

Provides request/response logging with correlation IDs and structured output.
"""
from __future__ import annotations

import json
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

import structlog

from src.precedent.config import settings


def setup_structlog() -> None:
    """Configure structlog for JSON output."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        setup_structlog()
        self.logger = structlog.get_logger(__name__)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())

        # Add correlation ID to request state
        request.state.correlation_id = correlation_id

        # Start timer
        start_time = time.time()

        # Extract request info
        method = request.method
        url = str(request.url)
        headers = dict(request.headers)

        # Remove sensitive headers for logging
        safe_headers = {
            k: v for k, v in headers.items()
            if k.lower() not in ('authorization', 'cookie', 'x-api-key', 'x-auth-token')
        }

        # Log request
        self.logger.info(
            "Request started",
            correlation_id=correlation_id,
            method=method,
            url=url,
            headers=safe_headers,
            client_host=request.client.host if request.client else None,
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate latency
            process_time = time.time() - start_time

            # Log response
            self.logger.info(
                "Request completed",
                correlation_id=correlation_id,
                method=method,
                url=url,
                status_code=response.status_code,
                process_time=process_time,
                response_size=response.headers.get("content-length"),
            )

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            return response

        except Exception as exc:
            # Calculate latency
            process_time = time.time() - start_time

            # Log exception
            self.logger.error(
                "Request failed",
                correlation_id=correlation_id,
                method=method,
                url=url,
                process_time=process_time,
                exc_info=exc,
            )

            # Re-raise the exception
            raise