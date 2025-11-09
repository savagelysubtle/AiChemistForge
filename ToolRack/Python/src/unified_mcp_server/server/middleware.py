"""Middleware system for the unified MCP server.

Provides request/response interception, rate limiting, authentication,
and other cross-cutting concerns following MCP best practices.
"""

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Protocol

from ..utils.exceptions import ToolError, ValidationError

logger = logging.getLogger("mcp.server.middleware")


class Middleware(Protocol):
    """Protocol for middleware implementations."""

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request before it reaches the handler.

        Args:
            request: Request dictionary

        Returns:
            Modified request dictionary

        Raises:
            Exception: If request should be rejected
        """
        ...

    async def process_response(
        self, request: Dict[str, Any], response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a response before it's sent to the client.

        Args:
            request: Original request dictionary
            response: Response dictionary

        Returns:
            Modified response dictionary
        """
        ...

    async def process_error(
        self, request: Dict[str, Any], error: Exception
    ) -> Dict[str, Any]:
        """Process an error that occurred during request handling.

        Args:
            request: Original request dictionary
            error: Exception that occurred

        Returns:
            Error response dictionary
        """
        ...


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    max_requests: int = 100
    window_seconds: float = 60.0
    per_tool: bool = False  # If True, rate limit per tool; if False, global


class RateLimitingMiddleware:
    """Middleware for rate limiting requests."""

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """Initialize rate limiting middleware.

        Args:
            config: Rate limit configuration
        """
        self.config = config or RateLimitConfig()
        self._request_counts: Dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process request with rate limiting.

        Args:
            request: Request dictionary

        Returns:
            Request dictionary

        Raises:
            ToolError: If rate limit exceeded
        """
        # Determine key for rate limiting
        if self.config.per_tool:
            tool_name = request.get("method", "unknown")
            key = f"tool:{tool_name}"
        else:
            key = "global"

        async with self._lock:
            now = time.time()
            window_start = now - self.config.window_seconds

            # Clean old requests
            self._request_counts[key] = [
                ts for ts in self._request_counts[key] if ts > window_start
            ]

            # Check rate limit
            if len(self._request_counts[key]) >= self.config.max_requests:
                raise ToolError(
                    f"Rate limit exceeded: {len(self._request_counts[key])} requests "
                    f"in the last {self.config.window_seconds}s "
                    f"(limit: {self.config.max_requests})"
                )

            # Record request
            self._request_counts[key].append(now)

        return request

    async def process_response(
        self, request: Dict[str, Any], response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process response (no-op for rate limiting).

        Args:
            request: Request dictionary
            response: Response dictionary

        Returns:
            Response dictionary
        """
        return response

    async def process_error(
        self, request: Dict[str, Any], error: Exception
    ) -> Dict[str, Any]:
        """Process error (no-op for rate limiting).

        Args:
            request: Request dictionary
            error: Exception

        Returns:
            Error response dictionary
        """
        return {"error": str(error)}


class TimingMiddleware:
    """Middleware for timing requests and adding timing information."""

    def __init__(self):
        """Initialize timing middleware."""
        self._start_times: Dict[str, float] = {}

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Record request start time.

        Args:
            request: Request dictionary

        Returns:
            Request dictionary
        """
        request_id = request.get("id", "unknown")
        self._start_times[request_id] = time.time()
        return request

    async def process_response(
        self, request: Dict[str, Any], response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add timing information to response.

        Args:
            request: Request dictionary
            response: Response dictionary

        Returns:
            Response dictionary with timing information
        """
        request_id = request.get("id", "unknown")
        if request_id in self._start_times:
            elapsed = time.time() - self._start_times[request_id]
            response["timing"] = {"elapsed_seconds": elapsed}
            del self._start_times[request_id]
        return response

    async def process_error(
        self, request: Dict[str, Any], error: Exception
    ) -> Dict[str, Any]:
        """Add timing information to error response.

        Args:
            request: Request dictionary
            error: Exception

        Returns:
            Error response dictionary with timing information
        """
        request_id = request.get("id", "unknown")
        if request_id in self._start_times:
            elapsed = time.time() - self._start_times[request_id]
            error_response = {"error": str(error), "timing": {"elapsed_seconds": elapsed}}
            del self._start_times[request_id]
            return error_response
        return {"error": str(error)}


class ValidationMiddleware:
    """Middleware for validating requests."""

    def __init__(self, validators: Optional[Dict[str, Callable[[Dict[str, Any]], bool]]] = None):
        """Initialize validation middleware.

        Args:
            validators: Dictionary mapping tool names to validator functions
        """
        self.validators = validators or {}

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Validate request.

        Args:
            request: Request dictionary

        Returns:
            Request dictionary

        Raises:
            ValidationError: If validation fails
        """
        method = request.get("method", "")
        if method in self.validators:
            validator = self.validators[method]
            if not validator(request):
                raise ValidationError(f"Validation failed for method: {method}")

        return request

    async def process_response(
        self, request: Dict[str, Any], response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process response (no-op for validation).

        Args:
            request: Request dictionary
            response: Response dictionary

        Returns:
            Response dictionary
        """
        return response

    async def process_error(
        self, request: Dict[str, Any], error: Exception
    ) -> Dict[str, Any]:
        """Process error (no-op for validation).

        Args:
            request: Request dictionary
            error: Exception

        Returns:
            Error response dictionary
        """
        return {"error": str(error)}


class MetricsMiddleware:
    """Middleware for collecting metrics."""

    def __init__(self):
        """Initialize metrics middleware."""
        try:
            from .metrics import get_metrics_collector

            self.metrics_collector = get_metrics_collector()
        except ImportError:
            self.metrics_collector = None
            logger.warning("Metrics collector not available")

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process request (no-op for metrics).

        Args:
            request: Request dictionary

        Returns:
            Request dictionary
        """
        return request

    async def process_response(
        self, request: Dict[str, Any], response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record metrics for successful request.

        Args:
            request: Request dictionary
            response: Response dictionary

        Returns:
            Response dictionary
        """
        if self.metrics_collector:
            method = request.get("method", "unknown")
            timing = response.get("timing", {})
            latency = timing.get("elapsed_seconds", 0.0)
            asyncio.create_task(
                self.metrics_collector.record_tool_call(method, latency, error=False)
            )
        return response

    async def process_error(
        self, request: Dict[str, Any], error: Exception
    ) -> Dict[str, Any]:
        """Record metrics for failed request.

        Args:
            request: Request dictionary
            error: Exception

        Returns:
            Error response dictionary
        """
        if self.metrics_collector:
            method = request.get("method", "unknown")
            # Estimate latency from timing middleware if available
            latency = 0.0
            asyncio.create_task(
                self.metrics_collector.record_tool_call(method, latency, error=True)
            )
        return {"error": str(error)}


class MiddlewareChain:
    """Chain of middleware to process requests."""

    def __init__(self, middlewares: Optional[list[Middleware]] = None):
        """Initialize middleware chain.

        Args:
            middlewares: List of middleware instances
        """
        self.middlewares = middlewares or []

    def add(self, middleware: Middleware) -> None:
        """Add middleware to the chain.

        Args:
            middleware: Middleware instance
        """
        self.middlewares.append(middleware)
        logger.debug(f"Added middleware: {middleware.__class__.__name__}")

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process request through all middleware.

        Args:
            request: Request dictionary

        Returns:
            Processed request dictionary

        Raises:
            Exception: If any middleware rejects the request
        """
        processed_request = request
        for middleware in self.middlewares:
            processed_request = await middleware.process_request(processed_request)
        return processed_request

    async def process_response(
        self, request: Dict[str, Any], response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process response through all middleware (in reverse order).

        Args:
            request: Original request dictionary
            response: Response dictionary

        Returns:
            Processed response dictionary
        """
        processed_response = response
        for middleware in reversed(self.middlewares):
            processed_response = await middleware.process_response(
                request, processed_response
            )
        return processed_response

    async def process_error(
        self, request: Dict[str, Any], error: Exception
    ) -> Dict[str, Any]:
        """Process error through all middleware (in reverse order).

        Args:
            request: Original request dictionary
            error: Exception

        Returns:
            Error response dictionary
        """
        error_response = {"error": str(error)}
        for middleware in reversed(self.middlewares):
            error_response = await middleware.process_error(request, error)
        return error_response


# Global middleware chain instance
_middleware_chain: Optional[MiddlewareChain] = None


def get_middleware_chain() -> MiddlewareChain:
    """Get the global middleware chain instance.

    Returns:
        MiddlewareChain instance
    """
    global _middleware_chain
    if _middleware_chain is None:
        _middleware_chain = MiddlewareChain()
    return _middleware_chain


def create_default_middleware_chain() -> MiddlewareChain:
    """Create default middleware chain with common middleware.

    Returns:
        MiddlewareChain instance
    """
    chain = MiddlewareChain()
    chain.add(TimingMiddleware())
    chain.add(MetricsMiddleware())
    return chain



