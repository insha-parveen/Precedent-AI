"""Rate limiting middleware for Precedent API.

Implements token bucket algorithm for request rate limiting.
"""
from __future__ import annotations

import time
from typing import Callable, Optional, Dict, Tuple
from collections import defaultdict

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.precedent.config import settings
from src.precedent.auth import AuthenticatedUser


class TokenBucket:
    """Token bucket implementation for rate limiting."""

    def __init__(self, rate: float, capacity: int):
        """
        Initialize token bucket.

        Args:
            rate: Tokens added per second
            capacity: Maximum number of tokens in bucket
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_updated = time.time()
        self._lock = False  # Simple lock for single-threaded async safety

    def consume(self, tokens: int = 1) -> bool:
        """
        Consume tokens from bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if not enough tokens
        """
        # Simple non-blocking check - if locked, assume we're processing
        if self._lock:
            return False

        self._lock = True
        try:
            now = time.time()
            # Add tokens based on elapsed time
            elapsed = now - self.last_updated
            self.tokens = min(self.capacity, self.tokens + (elapsed * self.rate))
            self.last_updated = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
        finally:
            self._lock = False


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""

    def __init__(self, app: ASGIApp, requests_per_minute: int = 60):
        """
        Initialize rate limiting middleware.

        Args:
            app: ASGI application
            requests_per_minute: Default requests per minute limit
        """
        super().__init__(app)
        self.default_rate = requests_per_minute / 60.0  # Convert to per second
        self.default_capacity = requests_per_minute

        # Different limits for different endpoints
        self.limit_configs: Dict[str, Tuple[float, int]] = {
            # LLM endpoints - more restrictive
            "/api/chat": (self.default_rate * 0.3, self.default_capacity * 0.3),
            "/api/ask": (self.default_rate * 0.3, self.default_capacity * 0.3),

            # Search endpoints - moderate
            "/api/search": (self.default_rate * 0.7, self.default_capacity * 0.7),

            # Document retrieval - less restrictive
            "/api/document/": (self.default_rate * 1.5, self.default_capacity * 1.5),

            # Admin endpoints - configurable
            "/api/admin/": (self.default_rate * 0.5, self.default_capacity * 0.5),

            # Health checks - unrestricted
            "/health": (float('inf'), float('inf')),
            "/metrics": (float('inf'), float('inf')),
        }

        # Storage for buckets per key (tenant/user/IP)
        self.buckets: Dict[str, Dict[str, TokenBucket]] = defaultdict(dict)
        self._cleanup_time = time.time()

    def _get_identifier(self, request: Request) -> str:
        """
        Get identifier for rate limiting (tenant > user > IP).

        Returns:
            String identifier for bucket selection
        """
        # Try to get tenant from request state (set by tenancy middleware)
        tenant_id = getattr(request.state, 'tenant_id', None)
        if tenant_id:
            return f"tenant:{tenant_id}"

        # Try to get user from authenticated user
        auth_user = getattr(request.state, 'user', None)
        if isinstance(auth_user, AuthenticatedUser) and auth_user.user_id:
            return f"user:{auth_user.user_id}"

        # Fallback to IP address
        if request.client:
            return f"ip:{request.client.host}"

        return "unknown"

    def _get_endpoint_key(self, path: str) -> str:
        """
        Get the most specific matching endpoint configuration.

        Args:
            path: Request path

        Returns:
            Endpoint key for limit configuration
        """
        # Check for exact matches first
        if path in self.limit_configs:
            return path

        # Check for prefix matches
        for endpoint_prefix in self.limit_configs:
            if path.startswith(endpoint_prefix):
                return endpoint_prefix

        # Return default configuration key
        return "default"

    def _get_bucket(self, identifier: str, endpoint_key: str) -> TokenBucket:
        """
        Get or create token bucket for identifier and endpoint.

        Args:
            identifier: User/tenant/IP identifier
            endpoint_key: Endpoint configuration key

        Returns:
            TokenBucket instance
        """
        if endpoint_key not in self.buckets[identifier]:
            rate, capacity = self.limit_configs.get(
                endpoint_key,
                (self.default_rate, self.default_capacity)
            )
            self.buckets[identifier][endpoint_key] = TokenBucket(rate, capacity)

        return self.buckets[identifier][endpoint_key]

    def _cleanup_old_buckets(self) -> None:
        """Clean up old buckets to prevent memory leaks."""
        now = time.time()
        # Cleanup every 5 minutes
        if now - self._cleanup_time < 300:
            return

        cutoff = now - 1800  # 30 minutes
        to_delete = []

        for identifier, endpoint_dict in self.buckets.items():
            for endpoint_key, bucket in endpoint_dict.items():
                if bucket.last_updated < cutoff:
                    to_delete.append((identifier, endpoint_key))

        for identifier, endpoint_key in to_delete:
            del self.buckets[identifier][endpoint_key]
            # Remove identifier dict if empty
            if not self.buckets[identifier]:
                del self.buckets[identifier]

        self._cleanup_time = now

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for metrics endpoint to avoid recursion issues
        if request.url.path == "/metrics":
            return await call_next(request)

        # Periodic cleanup
        self._cleanup_old_buckets()

        # Get identifier and endpoint
        identifier = self._get_identifier(request)
        endpoint_key = self._get_endpoint_key(request.url.path)

        # Get bucket and try to consume token
        bucket = self._get_bucket(identifier, endpoint_key)

        if not bucket.consume(1):
            # Rate limit exceeded
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "Retry-After": "60",  # Suggest waiting 1 minute
                }
            )

        # Process request
        response = await call_next(request)
        return response