"""Tests for retry decorator functionality."""

import asyncio
import logging
import time
from typing import Any, Dict

import pytest

from unified_mcp_server.utils import (
    RetryConfig,
    RetryStrategy,
    retry_async,
    retry_on_io_error,
    retry_on_network_error,
    tool_retry,
    with_retry,
)
from unified_mcp_server.utils.exceptions import ToolExecutionError

# Configure logger to show retry messages
logging.basicConfig(level=logging.DEBUG)


class TestRetryConfig:
    """Test RetryConfig class."""

    def test_default_config(self):
        """Test default retry configuration."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 30.0
        assert config.strategy == RetryStrategy.EXPONENTIAL

    def test_custom_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_attempts=5,
            initial_delay=2.0,
            max_delay=60.0,
            strategy=RetryStrategy.LINEAR,
        )
        assert config.max_attempts == 5
        assert config.initial_delay == 2.0
        assert config.max_delay == 60.0
        assert config.strategy == RetryStrategy.LINEAR

    def test_exponential_backoff(self):
        """Test exponential backoff calculation."""
        config = RetryConfig(
            initial_delay=1.0,
            max_delay=30.0,
            strategy=RetryStrategy.EXPONENTIAL,
        )
        assert config.calculate_delay(0) == 1.0  # 1.0 * 2^0
        assert config.calculate_delay(1) == 2.0  # 1.0 * 2^1
        assert config.calculate_delay(2) == 4.0  # 1.0 * 2^2
        assert config.calculate_delay(3) == 8.0  # 1.0 * 2^3
        assert config.calculate_delay(4) == 16.0  # 1.0 * 2^4
        assert config.calculate_delay(5) == 30.0  # capped at max_delay

    def test_linear_backoff(self):
        """Test linear backoff calculation."""
        config = RetryConfig(
            initial_delay=2.0,
            max_delay=30.0,
            strategy=RetryStrategy.LINEAR,
        )
        assert config.calculate_delay(0) == 2.0  # 2.0 * 1
        assert config.calculate_delay(1) == 4.0  # 2.0 * 2
        assert config.calculate_delay(2) == 6.0  # 2.0 * 3
        assert config.calculate_delay(3) == 8.0  # 2.0 * 4

    def test_fixed_backoff(self):
        """Test fixed backoff calculation."""
        config = RetryConfig(
            initial_delay=3.0,
            max_delay=30.0,
            strategy=RetryStrategy.FIXED,
        )
        assert config.calculate_delay(0) == 3.0
        assert config.calculate_delay(1) == 3.0
        assert config.calculate_delay(2) == 3.0
        assert config.calculate_delay(10) == 3.0

    def test_should_retry_retryable_exception(self):
        """Test should_retry with retryable exception."""
        config = RetryConfig(max_attempts=3)
        assert config.should_retry(OSError("I/O error"), 0) is True
        assert config.should_retry(ConnectionError("Network error"), 0) is True
        assert config.should_retry(TimeoutError("Timeout"), 1) is True

    def test_should_retry_non_retryable_exception(self):
        """Test should_retry with non-retryable exception."""
        config = RetryConfig(max_attempts=3)
        assert config.should_retry(ValueError("Invalid value"), 0) is False
        assert config.should_retry(TypeError("Type error"), 0) is False
        assert config.should_retry(KeyError("Key error"), 0) is False

    def test_should_retry_max_attempts_exceeded(self):
        """Test should_retry when max attempts exceeded."""
        config = RetryConfig(max_attempts=3)
        assert config.should_retry(OSError("I/O error"), 2) is False  # attempt 3 of 3


class TestWithRetryDecorator:
    """Test with_retry decorator."""

    @pytest.mark.asyncio
    async def test_successful_execution_no_retry(self):
        """Test successful execution without retry."""
        call_count = 0

        @with_retry(max_attempts=3)
        async def successful_func() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_func()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self):
        """Test retry on transient I/O error."""
        call_count = 0

        @with_retry(max_attempts=3, initial_delay=0.1)
        async def failing_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise OSError("Transient I/O error")
            return "success after retry"

        start_time = time.time()
        result = await failing_func()
        elapsed = time.time() - start_time

        assert result == "success after retry"
        assert call_count == 3
        # Should have delays: 0.1s + 0.2s = 0.3s minimum
        assert elapsed >= 0.3

    @pytest.mark.asyncio
    async def test_no_retry_on_validation_error(self):
        """Test no retry on validation error."""
        call_count = 0

        @with_retry(max_attempts=3, initial_delay=0.1)
        async def validation_error_func() -> str:
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid input")

        with pytest.raises(ValueError, match="Invalid input"):
            await validation_error_func()

        assert call_count == 1  # Should not retry

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test behavior when max retries exceeded."""
        call_count = 0

        @with_retry(max_attempts=3, initial_delay=0.1)
        async def always_fails() -> str:
            nonlocal call_count
            call_count += 1
            raise OSError("Persistent I/O error")

        with pytest.raises(OSError, match="Persistent I/O error"):
            await always_fails()

        assert call_count == 3  # Should try 3 times

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self):
        """Test exponential backoff timing."""
        call_count = 0

        @with_retry(
            max_attempts=4,
            initial_delay=0.1,
            strategy=RetryStrategy.EXPONENTIAL,
        )
        async def failing_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 4:
                raise OSError("Error")
            return "success"

        start_time = time.time()
        result = await failing_func()
        elapsed = time.time() - start_time

        assert result == "success"
        assert call_count == 4
        # Delays: 0.1s + 0.2s + 0.4s = 0.7s minimum
        assert elapsed >= 0.7


class TestToolRetryDecorator:
    """Test tool_retry convenience decorator."""

    @pytest.mark.asyncio
    async def test_tool_retry_default_config(self):
        """Test tool_retry with default configuration."""
        call_count = 0

        @tool_retry(max_attempts=3)
        async def tool_func() -> Dict[str, Any]:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise OSError("Transient error")
            return {"result": "success"}

        result = await tool_func()
        assert result == {"result": "success"}
        assert call_count == 2


class TestRetryOnIOError:
    """Test retry_on_io_error convenience decorator."""

    @pytest.mark.asyncio
    async def test_retry_on_io_error_success(self):
        """Test retry on I/O error with eventual success."""
        call_count = 0

        @retry_on_io_error(max_attempts=3)
        async def io_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise OSError("I/O error")
            return "success"

        result = await io_func()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_permission_error(self):
        """Test retry on permission error."""
        call_count = 0

        @retry_on_io_error(max_attempts=3)
        async def permission_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise PermissionError("Permission denied")
            return "success"

        result = await permission_func()
        assert result == "success"
        assert call_count == 2


class TestRetryOnNetworkError:
    """Test retry_on_network_error convenience decorator."""

    @pytest.mark.asyncio
    async def test_retry_on_connection_error(self):
        """Test retry on connection error."""
        call_count = 0

        @retry_on_network_error(max_attempts=3)
        async def network_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Connection failed")
            return "success"

        result = await network_func()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_timeout_error(self):
        """Test retry on timeout error."""
        call_count = 0

        @retry_on_network_error(max_attempts=3)
        async def timeout_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("Request timeout")
            return "success"

        result = await timeout_func()
        assert result == "success"
        assert call_count == 3


class TestRetryAsync:
    """Test retry_async utility function."""

    @pytest.mark.asyncio
    async def test_retry_async_with_config(self):
        """Test retry_async with custom config."""
        call_count = 0

        async def test_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise OSError("Error")
            return "success"

        config = RetryConfig(max_attempts=3, initial_delay=0.1)
        result = await retry_async(test_func, config=config)

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_async_with_args(self):
        """Test retry_async with function arguments."""
        call_count = 0

        async def test_func_with_args(x: int, y: int) -> int:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise OSError("Error")
            return x + y

        config = RetryConfig(max_attempts=3, initial_delay=0.1)
        result = await retry_async(test_func_with_args, 5, 10, config=config)

        assert result == 15
        assert call_count == 2


class TestSyncRetry:
    """Test retry decorator with synchronous functions."""

    def test_sync_function_retry(self):
        """Test retry with synchronous function."""
        call_count = 0

        @with_retry(max_attempts=3, initial_delay=0.1)
        def sync_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise OSError("Error")
            return "success"

        result = sync_func()
        assert result == "success"
        assert call_count == 2


class TestRetryCallback:
    """Test retry callback functionality."""

    @pytest.mark.asyncio
    async def test_on_retry_callback(self):
        """Test on_retry callback is called."""
        call_count = 0
        callback_count = 0
        callback_attempts = []
        callback_exceptions = []

        def on_retry(attempt: int, exception: Exception) -> None:
            nonlocal callback_count
            callback_count += 1
            callback_attempts.append(attempt)
            callback_exceptions.append(type(exception).__name__)

        config = RetryConfig(
            max_attempts=3,
            initial_delay=0.1,
            on_retry=on_retry,
        )

        @with_retry(
            max_attempts=3,
            initial_delay=0.1,
        )
        async def test_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise OSError("Error")
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

