"""Retry decorator for tool error handling and resilience.

This module provides decorators and utilities for adding automatic retry logic
to MCP tools, improving reliability when transient errors occur.
"""

import asyncio
import functools
import logging
import time
from enum import Enum
from typing import Any, Callable, Dict, Optional, Tuple, Type, TypeVar, Union

from unified_mcp_server.utils.exceptions import (
    DatabaseConnectionError,
    FilesystemError,
    SecurityError,
    ToolExecutionError,
    TransportError,
    UnifiedMCPError,
)

logger = logging.getLogger("mcp.utils.retry")

T = TypeVar("T")


class RetryStrategy(Enum):
    """Retry strategy types."""

    LINEAR = "linear"  # Wait time increases linearly (1s, 2s, 3s)
    EXPONENTIAL = "exponential"  # Wait time doubles (1s, 2s, 4s, 8s)
    FIXED = "fixed"  # Wait time stays constant (1s, 1s, 1s)


# Default retryable exceptions (transient errors)
DEFAULT_RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    # Network/connection errors
    ConnectionError,
    TimeoutError,
    OSError,  # I/O errors
    # MCP-specific transient errors
    DatabaseConnectionError,
    TransportError,
    # Generic filesystem errors that might be transient
    PermissionError,  # Might be temporary file locks
    BlockingIOError,
)

# Non-retryable exceptions (permanent errors)
NON_RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    # Validation errors - these won't fix themselves
    ValueError,
    TypeError,
    KeyError,
    AttributeError,
    # Security errors - don't retry security violations
    SecurityError,
)


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
        non_retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
        on_retry: Optional[Callable[[int, Exception], None]] = None,
        backoff_multiplier: float = 2.0,
    ):
        """Initialize retry configuration.

        Args:
            max_attempts: Maximum number of attempts (including initial attempt)
            initial_delay: Initial delay in seconds before first retry
            max_delay: Maximum delay between retries in seconds
            strategy: Retry strategy (linear, exponential, fixed)
            retryable_exceptions: Tuple of exception types that should trigger retries
            non_retryable_exceptions: Tuple of exception types that should NOT retry
            on_retry: Optional callback function called before each retry
            backoff_multiplier: Multiplier for exponential backoff (default: 2.0)
        """
        self.max_attempts = max(1, max_attempts)
        self.initial_delay = max(0.0, initial_delay)
        self.max_delay = max(initial_delay, max_delay)
        self.strategy = strategy
        self.retryable_exceptions = (
            retryable_exceptions
            if retryable_exceptions is not None
            else DEFAULT_RETRYABLE_EXCEPTIONS
        )
        self.non_retryable_exceptions = (
            non_retryable_exceptions
            if non_retryable_exceptions is not None
            else NON_RETRYABLE_EXCEPTIONS
        )
        self.on_retry = on_retry
        self.backoff_multiplier = backoff_multiplier

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        if self.strategy == RetryStrategy.FIXED:
            return min(self.initial_delay, self.max_delay)
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.initial_delay * (attempt + 1)
        else:  # EXPONENTIAL
            delay = self.initial_delay * (self.backoff_multiplier**attempt)

        return min(delay, self.max_delay)

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if an exception should trigger a retry.

        Args:
            exception: The exception that was raised
            attempt: Current attempt number (0-indexed)

        Returns:
            True if should retry, False otherwise
        """
        # Check if we've exceeded max attempts
        if attempt >= self.max_attempts - 1:
            return False

        # Check if exception is explicitly non-retryable
        if isinstance(exception, self.non_retryable_exceptions):
            return False

        # Check if exception is explicitly retryable
        if isinstance(exception, self.retryable_exceptions):
            return True

        # Default: don't retry unless explicitly retryable
        return False


def with_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    non_retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    backoff_multiplier: float = 2.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to add retry logic to async functions (MCP tools).

    This decorator automatically retries failed tool executions up to max_attempts times,
    with configurable backoff strategies and exception filtering.

    Args:
        max_attempts: Maximum number of attempts (including initial attempt)
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay between retries in seconds
        strategy: Retry strategy (linear, exponential, fixed)
        retryable_exceptions: Tuple of exception types that should trigger retries
        non_retryable_exceptions: Tuple of exception types that should NOT retry
        backoff_multiplier: Multiplier for exponential backoff (default: 2.0)

    Returns:
        Decorated function with retry logic

    Example:
        ```python
        @with_retry(max_attempts=3, strategy=RetryStrategy.EXPONENTIAL)
        @mcp.tool()
        async def my_tool(arg: str) -> Dict[str, Any]:
            # Tool implementation
            return {"result": "success"}
        ```
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Create retry config
        config = RetryConfig(
            max_attempts=max_attempts,
            initial_delay=initial_delay,
            max_delay=max_delay,
            strategy=strategy,
            retryable_exceptions=retryable_exceptions,
            non_retryable_exceptions=non_retryable_exceptions,
            backoff_multiplier=backoff_multiplier,
        )

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            """Async wrapper with retry logic."""
            last_exception: Optional[Exception] = None
            tool_name = func.__name__

            for attempt in range(config.max_attempts):
                try:
                    # Execute the tool
                    result = await func(*args, **kwargs)

                    # Log successful retry if this wasn't the first attempt
                    if attempt > 0:
                        logger.info(
                            f"Tool '{tool_name}' succeeded on attempt {attempt + 1}/{config.max_attempts}"
                        )

                    return result

                except Exception as e:
                    last_exception = e

                    # Check if we should retry
                    if not config.should_retry(e, attempt):
                        # Log non-retryable error
                        if attempt == 0:
                            logger.debug(
                                f"Tool '{tool_name}' failed with non-retryable error: {type(e).__name__}: {e}"
                            )
                        else:
                            logger.error(
                                f"Tool '{tool_name}' failed after {attempt + 1} attempts: {type(e).__name__}: {e}"
                            )
                        # Re-raise non-retryable or final attempt exception
                        raise

                    # Calculate delay for retry
                    delay = config.calculate_delay(attempt)

                    # Log retry attempt
                    logger.warning(
                        f"Tool '{tool_name}' failed on attempt {attempt + 1}/{config.max_attempts} "
                        f"with {type(e).__name__}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )

                    # Call retry callback if provided
                    if config.on_retry:
                        try:
                            config.on_retry(attempt, e)
                        except Exception as callback_error:
                            logger.error(
                                f"Error in retry callback: {callback_error}",
                                exc_info=True,
                            )

                    # Wait before retry
                    await asyncio.sleep(delay)

            # Should never reach here, but just in case
            if last_exception:
                logger.error(
                    f"Tool '{tool_name}' failed after {config.max_attempts} attempts"
                )
                raise last_exception
            else:
                raise ToolExecutionError(
                    f"Tool '{tool_name}' failed after {config.max_attempts} attempts",
                    error_code="MAX_RETRIES_EXCEEDED",
                )

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            """Sync wrapper with retry logic."""
            last_exception: Optional[Exception] = None
            tool_name = func.__name__

            for attempt in range(config.max_attempts):
                try:
                    # Execute the tool
                    result = func(*args, **kwargs)

                    # Log successful retry if this wasn't the first attempt
                    if attempt > 0:
                        logger.info(
                            f"Tool '{tool_name}' succeeded on attempt {attempt + 1}/{config.max_attempts}"
                        )

                    return result

                except Exception as e:
                    last_exception = e

                    # Check if we should retry
                    if not config.should_retry(e, attempt):
                        # Log non-retryable error
                        if attempt == 0:
                            logger.debug(
                                f"Tool '{tool_name}' failed with non-retryable error: {type(e).__name__}: {e}"
                            )
                        else:
                            logger.error(
                                f"Tool '{tool_name}' failed after {attempt + 1} attempts: {type(e).__name__}: {e}"
                            )
                        # Re-raise non-retryable or final attempt exception
                        raise

                    # Calculate delay for retry
                    delay = config.calculate_delay(attempt)

                    # Log retry attempt
                    logger.warning(
                        f"Tool '{tool_name}' failed on attempt {attempt + 1}/{config.max_attempts} "
                        f"with {type(e).__name__}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )

                    # Call retry callback if provided
                    if config.on_retry:
                        try:
                            config.on_retry(attempt, e)
                        except Exception as callback_error:
                            logger.error(
                                f"Error in retry callback: {callback_error}",
                                exc_info=True,
                            )

                    # Wait before retry
                    time.sleep(delay)

            # Should never reach here, but just in case
            if last_exception:
                logger.error(
                    f"Tool '{tool_name}' failed after {config.max_attempts} attempts"
                )
                raise last_exception
            else:
                raise ToolExecutionError(
                    f"Tool '{tool_name}' failed after {config.max_attempts} attempts",
                    error_code="MAX_RETRIES_EXCEEDED",
                )

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


def tool_retry(
    max_attempts: int = 3,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Simplified retry decorator specifically for MCP tools.

    This is a convenience wrapper around `with_retry` with sensible defaults
    for MCP tool usage.

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        strategy: Retry strategy (default: EXPONENTIAL)

    Returns:
        Decorated function with retry logic

    Example:
        ```python
        @tool_retry(max_attempts=3)
        @mcp.tool()
        async def file_tree(path: str) -> Dict[str, Any]:
            # Tool implementation
            return {"tree": "..."}
        ```
    """
    return with_retry(
        max_attempts=max_attempts,
        initial_delay=1.0,
        max_delay=30.0,
        strategy=strategy,
    )


# Convenience retry decorators for common scenarios
def retry_on_io_error(max_attempts: int = 3) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Retry decorator specifically for I/O errors.

    Args:
        max_attempts: Maximum number of attempts (default: 3)

    Returns:
        Decorated function with retry logic
    """
    return with_retry(
        max_attempts=max_attempts,
        strategy=RetryStrategy.EXPONENTIAL,
        retryable_exceptions=(OSError, IOError, FilesystemError, PermissionError),
    )


def retry_on_network_error(max_attempts: int = 3) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Retry decorator specifically for network errors.

    Args:
        max_attempts: Maximum number of attempts (default: 3)

    Returns:
        Decorated function with retry logic
    """
    return with_retry(
        max_attempts=max_attempts,
        strategy=RetryStrategy.EXPONENTIAL,
        retryable_exceptions=(
            ConnectionError,
            TimeoutError,
            DatabaseConnectionError,
            TransportError,
        ),
    )


# Utility functions for manual retry logic
async def retry_async(
    func: Callable[..., T],
    *args: Any,
    config: Optional[RetryConfig] = None,
    **kwargs: Any,
) -> T:
    """Manually retry an async function with specified config.

    Args:
        func: Async function to retry
        *args: Positional arguments for func
        config: Retry configuration (uses defaults if None)
        **kwargs: Keyword arguments for func

    Returns:
        Result of successful function execution

    Raises:
        Last exception if all retries fail
    """
    if config is None:
        config = RetryConfig()

    last_exception: Optional[Exception] = None
    func_name = func.__name__

    for attempt in range(config.max_attempts):
        try:
            result = await func(*args, **kwargs)
            if attempt > 0:
                logger.info(
                    f"Function '{func_name}' succeeded on attempt {attempt + 1}/{config.max_attempts}"
                )
            return result

        except Exception as e:
            last_exception = e

            if not config.should_retry(e, attempt):
                raise

            delay = config.calculate_delay(attempt)
            logger.warning(
                f"Function '{func_name}' failed on attempt {attempt + 1}/{config.max_attempts}. "
                f"Retrying in {delay:.2f}s..."
            )

            if config.on_retry:
                config.on_retry(attempt, e)

            await asyncio.sleep(delay)

    if last_exception:
        raise last_exception
    raise ToolExecutionError(
        f"Function '{func_name}' failed after {config.max_attempts} attempts"
    )

