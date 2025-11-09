"""Logging setup for the unified MCP server.

Following 1000-mcp-stdio-logging.mdc guidelines:
- Keep logging simple for local MCP servers
- Direct logs to stderr to avoid stdio JSON-RPC interference
- Prioritize simplicity over complex logging frameworks

Enhanced with:
- Correlation ID propagation for request tracing
- Structured logging with context fields
- Performance timing decorators
"""

import contextlib
import contextvars
import functools
import logging
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar

# Context variable for correlation ID
correlation_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id", default=None
)

# Context variable for additional context
log_context: contextvars.ContextVar[Optional[Dict[str, Any]]] = contextvars.ContextVar(
    "log_context", default=None
)

T = TypeVar("T")


def setup_simple_logging(
    name: str, level: str = "INFO", use_stderr: bool = True
) -> logging.Logger:
    """Set up simple logging for MCP server components.

    Per 1000-mcp-stdio-logging.mdc: Keep local server logging straightforward.

    Args:
        name: Logger name (typically module name)
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        use_stderr: Whether to use stderr (recommended for MCP stdio compatibility)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper()))

    # Simple formatter - avoid complexity per MCP guidelines
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S"
    )

    # Use stderr to keep stdout clear for JSON-RPC (MCP stdio transport requirement)
    stream = sys.stderr if use_stderr else sys.stdout
    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def setup_logging(
    name: str,
    level: str = "INFO",
    log_to_file: bool = False,
    log_file_path: Optional[Path] = None,
) -> logging.Logger:
    """Set up structured logging for MCP server components.

    This function provides backward compatibility while encouraging
    the use of setup_simple_logging() for new code.

    Args:
        name: Logger name (typically module name)
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_to_file: Whether to log to file in addition to stderr
        log_file_path: Path to log file (defaults to logs/{name}.log)

    Returns:
        Configured logger instance
    """
    # For local MCP servers, prefer simple logging per 1000-mcp-stdio-logging.mdc
    if not log_to_file:
        return setup_simple_logging(name, level)

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (stderr for MCP compatibility)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (when specifically requested)
    if log_to_file:
        if log_file_path is None:
            log_file_path = Path("logs") / f"{name}.log"

        log_file_path.parent.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Get a simple logger for MCP components.

    Convenience function that follows MCP stdio logging best practices.

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Configured logger instance
    """
    return setup_simple_logging(name, level)


class ContextualFormatter(logging.Formatter):
    """Log formatter that includes correlation ID and context."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with correlation ID and context."""
        # Add correlation ID if available
        corr_id = correlation_id.get()
        if corr_id:
            record.correlation_id = corr_id
        else:
            record.correlation_id = ""

        # Add context if available
        ctx = log_context.get()
        if ctx:
            record.context = " | ".join(f"{k}={v}" for k, v in ctx.items())
        else:
            record.context = ""

        # Format with correlation ID and context
        if hasattr(record, "correlation_id") and record.correlation_id:
            if hasattr(record, "context") and record.context:
                return super().format(record).replace(
                    "%(message)s",
                    f"[{record.correlation_id}] {record.context} | %(message)s",
                )
            return super().format(record).replace(
                "%(message)s", f"[{record.correlation_id}] %(message)s"
            )
        elif hasattr(record, "context") and record.context:
            return super().format(record).replace(
                "%(message)s", f"{record.context} | %(message)s"
            )

        return super().format(record)


def setup_contextual_logging(
    name: str, level: str = "INFO", use_stderr: bool = True
) -> logging.Logger:
    """Set up contextual logging with correlation ID support.

    Args:
        name: Logger name
        level: Logging level
        use_stderr: Whether to use stderr

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper()))

    # Use contextual formatter
    formatter = ContextualFormatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S"
    )

    stream = sys.stderr if use_stderr else sys.stdout
    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def set_correlation_id(corr_id: Optional[str] = None) -> str:
    """Set correlation ID for current context.

    Args:
        corr_id: Optional correlation ID (generates new one if None)

    Returns:
        Correlation ID
    """
    if corr_id is None:
        corr_id = str(uuid.uuid4())[:8]
    correlation_id.set(corr_id)
    return corr_id


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID.

    Returns:
        Correlation ID or None
    """
    return correlation_id.get()


def add_log_context(key: str, value: Any) -> None:
    """Add context to current logging context.

    Args:
        key: Context key
        value: Context value
    """
    ctx = log_context.get()
    if ctx is None:
        ctx = {}
    ctx[key] = value
    log_context.set(ctx)


def clear_log_context() -> None:
    """Clear current logging context."""
    log_context.set({})


def timed(
    logger: Optional[logging.Logger] = None,
    level: int = logging.INFO,
    log_args: bool = False,
    log_result: bool = False,
):
    """Decorator for timing function execution.

    Args:
        logger: Logger instance (creates one if None)
        level: Logging level
        log_args: Whether to log function arguments
        log_result: Whether to log function result

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        func_logger = logger or logging.getLogger(func.__module__)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            corr_id = get_correlation_id() or set_correlation_id()
            func_name = func.__name__

            # Log start
            if log_args:
                func_logger.log(
                    level,
                    f"Starting {func_name} with args={args}, kwargs={kwargs}",
                )
            else:
                func_logger.log(level, f"Starting {func_name}")

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start_time

                # Log completion
                if log_result:
                    func_logger.log(
                        level,
                        f"Completed {func_name} in {elapsed:.3f}s, result={result}",
                    )
                else:
                    func_logger.log(level, f"Completed {func_name} in {elapsed:.3f}s")

                return result
            except Exception as e:
                elapsed = time.time() - start_time
                func_logger.error(
                    f"Failed {func_name} after {elapsed:.3f}s: {e}",
                    exc_info=True,
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            corr_id = get_correlation_id() or set_correlation_id()
            func_name = func.__name__

            # Log start
            if log_args:
                func_logger.log(
                    level,
                    f"Starting {func_name} with args={args}, kwargs={kwargs}",
                )
            else:
                func_logger.log(level, f"Starting {func_name}")

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time

                # Log completion
                if log_result:
                    func_logger.log(
                        level,
                        f"Completed {func_name} in {elapsed:.3f}s, result={result}",
                    )
                else:
                    func_logger.log(level, f"Completed {func_name} in {elapsed:.3f}s")

                return result
            except Exception as e:
                elapsed = time.time() - start_time
                func_logger.error(
                    f"Failed {func_name} after {elapsed:.3f}s: {e}",
                    exc_info=True,
                )
                raise

        if hasattr(func, "__code__") and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        return sync_wrapper

    return decorator


@contextlib.contextmanager
def log_context_manager(**context_vars):
    """Context manager for adding temporary log context.

    Usage:
        with log_context_manager(user_id="123", request_id="abc"):
            logger.info("This log will include user_id and request_id")
    """
    old_context = log_context.get()
    if old_context is None:
        old_context = {}
    old_context = old_context.copy()
    new_context = {**old_context, **context_vars}
    token = log_context.set(new_context)
    try:
        yield
    finally:
        log_context.set(old_context)
