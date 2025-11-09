# Performance Tuning Guide

## Overview

This guide covers performance optimization strategies for the AiChemistForge MCP server.

## Configuration Tuning

### Operation Timeouts

```bash
# Default: 30 seconds
OPERATION_TIMEOUT=30.0

# For faster operations, reduce timeout
OPERATION_TIMEOUT=10.0

# For slow operations (large file processing), increase timeout
OPERATION_TIMEOUT=60.0
```

### Retry Configuration

```bash
# Number of retry attempts
RETRY_MAX_ATTEMPTS=3

# Initial delay between retries (seconds)
RETRY_INITIAL_DELAY=1.0

# Maximum delay between retries (seconds)
RETRY_MAX_DELAY=60.0
```

### Concurrency Limits

```bash
# Maximum concurrent operations
MAX_CONCURRENT_OPERATIONS=10

# Increase for high-performance servers
MAX_CONCURRENT_OPERATIONS=50

# Decrease for resource-constrained environments
MAX_CONCURRENT_OPERATIONS=5
```

### Cache Configuration

```bash
# Maximum cache size (entries)
CACHE_MAX_SIZE=1000

# Default cache TTL (seconds)
CACHE_DEFAULT_TTL=300.0

# For frequently accessed data, increase TTL
CACHE_DEFAULT_TTL=600.0

# For rapidly changing data, decrease TTL
CACHE_DEFAULT_TTL=60.0
```

## Async Optimization

### Concurrent File Processing

Tools that process multiple files should use concurrent processing:

```python
import asyncio
from unified_mcp_server.server.config import config

async def process_files(files: List[str]):
    semaphore = asyncio.Semaphore(config.max_concurrent_operations)

    async def process_file(file: str):
        async with semaphore:
            # Process file
            pass

    await asyncio.gather(*[process_file(f) for f in files])
```

### Batch Operations

Group operations into batches to reduce overhead:

```python
async def batch_operation(items: List[Any], batch_size: int = 10):
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        await process_batch(batch)
```

## Caching Strategies

### Function Result Caching

Use the `@cached` decorator for expensive operations:

```python
from unified_mcp_server.utils.caching import cached

@cached(ttl=300.0)
async def expensive_operation(param: str):
    # Expensive computation
    return result
```

### Cache Warming

Warm up cache on startup for frequently accessed data:

```python
from unified_mcp_server.utils.caching import cache_manager

async def warmup_cache():
    await cache_manager.warmup([
        load_frequently_used_data,
        precompute_common_results,
    ])
```

## Resource Pooling

### Connection Pooling

Use resource pools for external service connections:

```python
from unified_mcp_server.server.resources import get_resource_manager

resource_manager = get_resource_manager()

# Create a connection pool
pool = resource_manager.register_pool(
    "database",
    factory=create_db_connection,
    max_size=10,
    min_size=2,
)

# Use in async context
async with pool.acquire_context() as conn:
    # Use connection
    pass
```

## Monitoring Performance

### Metrics Collection

Enable metrics to track performance:

```bash
METRICS_ENABLED=true
```

Access metrics programmatically:

```python
from unified_mcp_server.server.metrics import get_metrics_collector

collector = get_metrics_collector()
tool_metrics = collector.get_tool_metrics("tool_name")
server_health = collector.get_server_health()
```

### Performance Timing

Use the `@timed` decorator for function timing:

```python
from unified_mcp_server.server.logging import timed

@timed(log_args=True)
async def my_function(param: str):
    # Function implementation
    pass
```

## Profiling

### Python Profiling

Use cProfile for detailed profiling:

```bash
python -m cProfile -o profile.stats -m unified_mcp_server.main
```

### Memory Profiling

Use memory_profiler for memory analysis:

```python
from memory_profiler import profile

@profile
async def memory_intensive_function():
    # Function implementation
    pass
```

## Optimization Checklist

- [ ] Configure appropriate timeouts for operations
- [ ] Set retry limits to prevent excessive retries
- [ ] Configure concurrency limits based on resources
- [ ] Enable caching for expensive operations
- [ ] Use concurrent processing for batch operations
- [ ] Implement connection pooling for external services
- [ ] Enable metrics collection for monitoring
- [ ] Profile slow operations to identify bottlenecks
- [ ] Use async/await for all I/O operations
- [ ] Batch operations to reduce overhead

## Common Performance Issues

### High Memory Usage

**Symptoms:**
- Memory usage grows over time
- Server becomes slow

**Solutions:**
- Reduce cache size
- Clear cache periodically
- Use generators instead of lists
- Limit concurrent operations

### Slow Tool Execution

**Symptoms:**
- High latency for tool calls
- Timeout errors

**Solutions:**
- Increase operation timeout
- Optimize tool implementation
- Use caching for repeated operations
- Process operations concurrently

### High CPU Usage

**Symptoms:**
- High CPU utilization
- Slow response times

**Solutions:**
- Reduce concurrent operations
- Optimize CPU-intensive operations
- Use caching to avoid recomputation
- Profile and optimize hot paths

## Performance Testing

### Load Testing

Use tools like `locust` or `wrk` for load testing:

```bash
# Install locust
pip install locust

# Run load test
locust -f load_test.py
```

### Benchmarking

Create benchmarks for critical operations:

```python
import time
import asyncio

async def benchmark_operation():
    start = time.time()
    await operation()
    elapsed = time.time() - start
    print(f"Operation took {elapsed:.3f}s")
```

## Best Practices

1. **Measure First**: Profile before optimizing
2. **Cache Strategically**: Cache expensive, frequently accessed data
3. **Use Async**: All I/O operations should be async
4. **Limit Concurrency**: Don't overwhelm system resources
5. **Monitor Metrics**: Track performance over time
6. **Optimize Hot Paths**: Focus on frequently executed code
7. **Batch Operations**: Group related operations
8. **Use Connection Pools**: Reuse connections for external services



