"""Comprehensive error handling framework for the unified MCP server.

Provides retry logic, timeouts, circuit breakers, and graceful degradation
following MCP best practices for resilient server operation.
"""

import asyncio
import functools
import logging
import time
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar, Union

from ..utils.exceptions import (
    ToolError,
    ToolExecutionError,
    TransportError,
    ValidationError,
)

logger = logging.getLogger("mcp.server.error_handling")

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker pattern for preventing cascading failures."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type[Exception] = Exception,
    ):
        """Initialize a circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type that triggers circuit breaker
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
        self.success_count = 0
        self._lock = asyncio.Lock()

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute a function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        async with self._lock:
            # Check if circuit should transition to half-open
            if self.state == CircuitState.OPEN:
                if (
                    self.last_failure_time
                    and time.time() - self.last_failure_time >= self.recovery_timeout
                ):
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info("Circuit breaker transitioning to HALF_OPEN state")
                else:
                    raise TransportError(
                        f"Circuit breaker is OPEN (failed {self.failure_count} times, "
                        f"waiting {self.recovery_timeout}s before retry)"
                    )

        try:
            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Success - reset failure count
            async with self._lock:
                if self.state == CircuitState.HALF_OPEN:
                    self.success_count += 1
                    if self.success_count >= 2:  # Require 2 successes to close
                        self.state = CircuitState.CLOSED
                        self.failure_count = 0
                        logger.info("Circuit breaker transitioning to CLOSED state")
                elif self.state == CircuitState.CLOSED:
                    self.failure_count = 0  # Reset on success

            return result

        except self.expected_exception as e:
            async with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN
                    logger.warning(
                        f"Circuit breaker OPENED after {self.failure_count} failures"
                    )

            raise

    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state.

        Returns:
            Dictionary with state information
        """
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time,
            "success_count": self.success_count,
        }


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on: tuple[type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    """Decorator for retrying failed operations with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        exponential_base: Base for exponential backoff
        jitter: Add random jitter to delays
        retry_on: Tuple of exception types to retry on
        on_retry: Optional callback called on each retry

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            last_exception = None
            delay = initial_delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        break

                    # Calculate delay with exponential backoff
                    if jitter:
                        import random

                        jitter_amount = delay * 0.1 * random.random()
                        actual_delay = delay + jitter_amount
                    else:
                        actual_delay = delay

                    actual_delay = min(actual_delay, max_delay)

                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt}/{max_attempts}), "
                        f"retrying in {actual_delay:.2f}s: {e}"
                    )

                    if on_retry:
                        try:
                            if asyncio.iscoroutinefunction(on_retry):
                                await on_retry(e, attempt)
                            else:
                                on_retry(e, attempt)
                        except Exception as retry_callback_error:
                            logger.error(
                                f"Error in retry callback: {retry_callback_error}",
                                exc_info=True,
                            )

                    await asyncio.sleep(actual_delay)
                    delay *= exponential_base

            # All attempts failed
            raise ToolExecutionError(
                f"Function {func.__name__} failed after {max_attempts} attempts"
            ) from last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            last_exception = None
            delay = initial_delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        break

                    # Calculate delay with exponential backoff
                    if jitter:
                        import random

                        jitter_amount = delay * 0.1 * random.random()
                        actual_delay = delay + jitter_amount
                    else:
                        actual_delay = delay

                    actual_delay = min(actual_delay, max_delay)

                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt}/{max_attempts}), "
                        f"retrying in {actual_delay:.2f}s: {e}"
                    )

                    if on_retry:
                        try:
                            on_retry(e, attempt)
                        except Exception as retry_callback_error:
                            logger.error(
                                f"Error in retry callback: {retry_callback_error}",
                                exc_info=True,
                            )

                    time.sleep(actual_delay)
                    delay *= exponential_base

            # All attempts failed
            raise ToolExecutionError(
                f"Function {func.__name__} failed after {max_attempts} attempts"
            ) from last_exception

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def timeout(
    seconds: float = 30.0,
    timeout_error: type[Exception] = TimeoutError,
    on_timeout: Optional[Callable[[], None]] = None,
):
    """Decorator for adding timeout to operations.

    Args:
        seconds: Timeout in seconds
        timeout_error: Exception type to raise on timeout
        on_timeout: Optional callback called on timeout

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                logger.error(
                    f"Function {func.__name__} timed out after {seconds}s",
                    exc_info=True,
                )
                if on_timeout:
                    try:
                        if asyncio.iscoroutinefunction(on_timeout):
                            await on_timeout()
                        else:
                            on_timeout()
                    except Exception as callback_error:
                        logger.error(
                            f"Error in timeout callback: {callback_error}",
                            exc_info=True,
                        )
                raise timeout_error(
                    f"Operation timed out after {seconds} seconds"
                ) from None

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            # For sync functions, we can't easily add timeout without threading
            # So we'll just execute it and log a warning
            logger.warning(
                f"Timeout decorator applied to sync function {func.__name__}, "
                "timeout not enforced (consider making function async)"
            )
            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def graceful_degradation(
    fallback_value: Any = None,
    fallback_func: Optional[Callable[..., T]] = None,
    log_errors: bool = True,
):
    """Decorator for graceful degradation on errors.

    Args:
        fallback_value: Value to return on error
        fallback_func: Function to call on error (takes same args as original)
        log_errors: Whether to log errors

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.warning(
                        f"Function {func.__name__} failed, using graceful degradation: {e}",
                        exc_info=True,
                    )

                if fallback_func:
                    try:
                        if asyncio.iscoroutinefunction(fallback_func):
                            return await fallback_func(*args, **kwargs)
                        return fallback_func(*args, **kwargs)
                    except Exception as fallback_error:
                        logger.error(
                            f"Fallback function also failed: {fallback_error}",
                            exc_info=True,
                        )

                return fallback_value

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.warning(
                        f"Function {func.__name__} failed, using graceful degradation: {e}",
                        exc_info=True,
                    )

                if fallback_func:
                    try:
                        return fallback_func(*args, **kwargs)
                    except Exception as fallback_error:
                        logger.error(
                            f"Fallback function also failed: {fallback_error}",
                            exc_info=True,
                        )

                return fallback_value

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Convenience function for creating structured error responses
def create_error_response(
    error: Exception,
    error_code: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a structured error response.

    Args:
        error: Exception that occurred
        error_code: Optional error code
        context: Optional additional context

    Returns:
        Dictionary with error information
    """
    response = {
        "error": error.__class__.__name__,
        "message": str(error),
        "error_code": error_code or "UNKNOWN_ERROR",
    }

    if context:
        response["context"] = context

    # Add exception details if available
    if hasattr(error, "to_dict"):
        response.update(error.to_dict())

    return response



