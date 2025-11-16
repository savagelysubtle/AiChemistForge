# Retry Logic for MCP Tools

## Overview

The AiChemistForge Python MCP server includes a robust retry system that automatically retries failed tool executions up to 3 times before returning an error. This improves reliability when transient errors occur (network issues, temporary file locks, etc.) without requiring the LLM to manually retry tools.

## Key Features

- **Automatic Retries**: Tools automatically retry on transient errors
- **Smart Backoff**: Configurable retry strategies (exponential, linear, fixed)
- **Error Classification**: Distinguishes between retryable (transient) and non-retryable (permanent) errors
- **Logging**: Comprehensive logging of retry attempts for debugging
- **Zero Overhead**: No performance impact on successful executions

## Usage

### Basic Usage with `tool_retry`

The simplest way to add retry logic to a tool:

```python
from fastmcp import FastMCP
from unified_mcp_server.utils import tool_retry

def register_my_tool(mcp: FastMCP) -> None:
    @tool_retry(max_attempts=3)
    @mcp.tool()
    async def my_tool(arg: str) -> dict:
        # Tool implementation
        return {"result": "success"}
```

### I/O-Specific Retry

For tools that perform filesystem operations:

```python
from unified_mcp_server.utils import retry_on_io_error

def register_file_tool(mcp: FastMCP) -> None:
    @retry_on_io_error(max_attempts=3)
    @mcp.tool()
    async def file_tool(path: str) -> dict:
        # File operations
        return {"data": "..."}
```

### Network-Specific Retry

For tools that make network requests:

```python
from unified_mcp_server.utils import retry_on_network_error

def register_api_tool(mcp: FastMCP) -> None:
    @retry_on_network_error(max_attempts=3)
    @mcp.tool()
    async def api_tool(endpoint: str) -> dict:
        # API call
        return {"response": "..."}
```

### Advanced Configuration

For fine-grained control over retry behavior:

```python
from unified_mcp_server.utils import with_retry, RetryStrategy

def register_advanced_tool(mcp: FastMCP) -> None:
    @with_retry(
        max_attempts=5,
        initial_delay=2.0,
        max_delay=60.0,
        strategy=RetryStrategy.EXPONENTIAL,
        backoff_multiplier=2.0,
    )
    @mcp.tool()
    async def advanced_tool(data: str) -> dict:
        # Complex operation
        return {"status": "complete"}
```

## Retry Strategies

### Exponential Backoff (Default)

Delay doubles after each retry:
- Attempt 1: Wait 1s
- Attempt 2: Wait 2s
- Attempt 3: Wait 4s
- Attempt 4: Wait 8s

Best for network operations and external API calls.

```python
@with_retry(strategy=RetryStrategy.EXPONENTIAL)
```

### Linear Backoff

Delay increases linearly:
- Attempt 1: Wait 1s
- Attempt 2: Wait 2s
- Attempt 3: Wait 3s
- Attempt 4: Wait 4s

Best for resource contention scenarios.

```python
@with_retry(strategy=RetryStrategy.LINEAR)
```

### Fixed Delay

Same delay for all retries:
- Attempt 1: Wait 1s
- Attempt 2: Wait 1s
- Attempt 3: Wait 1s

Best for simple retry scenarios.

```python
@with_retry(strategy=RetryStrategy.FIXED)
```

## Error Classification

### Retryable Errors (Transient)

These errors trigger automatic retries:

- `OSError` - I/O errors (file access, disk issues)
- `ConnectionError` - Network connection failures
- `TimeoutError` - Request timeouts
- `PermissionError` - Temporary file locks
- `BlockingIOError` - Resource temporarily unavailable
- `DatabaseConnectionError` - Database connection issues
- `TransportError` - MCP transport errors

### Non-Retryable Errors (Permanent)

These errors do NOT trigger retries:

- `ValueError` - Invalid input values
- `TypeError` - Type mismatches
- `KeyError` - Missing dictionary keys
- `AttributeError` - Missing object attributes
- `SecurityError` - Security violations

These are validation or logic errors that won't be fixed by retrying.

## Logging

The retry system logs all retry attempts to stderr for debugging:

```
WARNING:mcp.tools.file_tree:Tool 'file_tree' failed on attempt 1/3 with OSError: Permission denied. Retrying in 1.00s...
WARNING:mcp.tools.file_tree:Tool 'file_tree' failed on attempt 2/3 with OSError: Permission denied. Retrying in 2.00s...
INFO:mcp.tools.file_tree:Tool 'file_tree' succeeded on attempt 3/3
```

## Applied to Existing Tools

The retry logic is currently applied to:

### Filesystem Tools

- **`file_tree`**: Retries on I/O errors (up to 3 attempts)
- **`codebase_ingest`**: Retries on I/O errors (up to 3 attempts)

Both use `@retry_on_io_error(max_attempts=3)` to handle transient filesystem issues like:
- Temporary file locks
- Network drive latency
- Disk I/O errors
- Permission conflicts

### Future Tools

Any new tools can easily add retry logic using the decorators above.

## Configuration

### Default Settings

- **Max Attempts**: 3 (including initial attempt)
- **Initial Delay**: 1.0 seconds
- **Max Delay**: 30.0 seconds
- **Strategy**: Exponential backoff
- **Backoff Multiplier**: 2.0

### Customization

You can customize retry behavior per tool:

```python
@with_retry(
    max_attempts=5,        # Try up to 5 times
    initial_delay=0.5,     # Start with 0.5s delay
    max_delay=10.0,        # Cap at 10s delay
    strategy=RetryStrategy.LINEAR,  # Linear backoff
)
```

## Testing

Comprehensive tests are available in `tests/test_retry.py`:

```bash
# Run retry tests
cd ToolRack/Python
uv run pytest tests/test_retry.py -v

# Run specific test
uv run pytest tests/test_retry.py::TestWithRetryDecorator::test_retry_on_transient_error -v
```

## Best Practices

### When to Use Retry Logic

✅ **Use retry for**:
- File system operations
- Network requests
- Database connections
- External API calls
- Resource contention scenarios

❌ **Don't use retry for**:
- Input validation
- Business logic errors
- Security checks
- Configuration errors

### Choosing Max Attempts

- **3 attempts**: Good default for most tools
- **5 attempts**: Network operations with high latency
- **1 attempt**: No retry (validation tools)

### Choosing Backoff Strategy

- **Exponential**: Network/API calls (prevents overwhelming servers)
- **Linear**: File system operations (steady retry pace)
- **Fixed**: Simple scenarios with predictable recovery

## Examples

### Example 1: File Tree Tool

```python
from unified_mcp_server.utils import retry_on_io_error

def register_file_tree_tool(mcp: FastMCP) -> None:
    @retry_on_io_error(max_attempts=3)
    @mcp.tool()
    async def file_tree(path: str) -> dict:
        # If this fails with OSError, it will retry up to 3 times
        # with exponential backoff (1s, 2s, 4s)
        target_path = Path(path).resolve()

        if not target_path.exists():
            # ValueError is NOT retryable - fails immediately
            raise ValueError(f"Path does not exist: {path}")

        # I/O operations that might fail transiently
        items = list(target_path.iterdir())
        return {"tree": format_tree(items)}
```

### Example 2: Custom Retry Logic

```python
from unified_mcp_server.utils import with_retry, RetryStrategy

def register_api_tool(mcp: FastMCP) -> None:
    @with_retry(
        max_attempts=5,
        initial_delay=2.0,
        strategy=RetryStrategy.EXPONENTIAL,
        retryable_exceptions=(ConnectionError, TimeoutError),
        non_retryable_exceptions=(ValueError, KeyError),
    )
    @mcp.tool()
    async def fetch_data(endpoint: str) -> dict:
        # Custom retry configuration for API calls
        response = await make_api_request(endpoint)
        return {"data": response}
```

## Manual Retry

For non-tool functions, use `retry_async`:

```python
from unified_mcp_server.utils import retry_async, RetryConfig

async def my_helper_function(arg: str) -> str:
    # Function that might fail
    return process_data(arg)

# Manually retry with config
config = RetryConfig(max_attempts=3, initial_delay=1.0)
result = await retry_async(my_helper_function, "data", config=config)
```

## Troubleshooting

### Retry Not Working

**Problem**: Tool doesn't retry on failure

**Solutions**:
1. Check that the decorator is applied **before** `@mcp.tool()`:
   ```python
   @retry_on_io_error(max_attempts=3)  # Must be BEFORE @mcp.tool()
   @mcp.tool()
   async def my_tool(...):
   ```

2. Verify the exception is retryable:
   ```python
   # Check logs for exception type
   # Ensure it's in DEFAULT_RETRYABLE_EXCEPTIONS
   ```

### Too Many Retries

**Problem**: Tool retries too many times, causing delays

**Solutions**:
1. Reduce max_attempts:
   ```python
   @tool_retry(max_attempts=2)  # Only retry once
   ```

2. Make error non-retryable if it's not transient:
   ```python
   @with_retry(
       non_retryable_exceptions=(MyCustomError,)
   )
   ```

### Logs Too Verbose

**Problem**: Too many retry log messages

**Solutions**:
1. Adjust log level in `.env`:
   ```
   MCP_LOG_LEVEL=INFO  # Reduces DEBUG messages
   ```

2. The retry system uses WARNING level for retries, so they'll still show

## Implementation Details

The retry system is implemented in `src/unified_mcp_server/utils/retry.py`:

- **`RetryConfig`**: Configuration class for retry behavior
- **`RetryStrategy`**: Enum for backoff strategies
- **`with_retry`**: Main decorator with full configuration
- **`tool_retry`**: Simplified decorator for MCP tools
- **`retry_on_io_error`**: Convenience decorator for I/O operations
- **`retry_on_network_error`**: Convenience decorator for network operations
- **`retry_async`**: Utility function for manual retries

All retry decorators work with both async and sync functions.

## Future Enhancements

Potential improvements:

- [ ] Circuit breaker pattern (stop retrying after sustained failures)
- [ ] Jitter in backoff (randomize delay to prevent thundering herd)
- [ ] Retry metrics collection (track retry rates)
- [ ] Conditional retry (retry based on error message/code)
- [ ] Retry budget (limit retries across all tools globally)

---

**Last Updated**: 2025-11-12
**Version**: 1.0.0

