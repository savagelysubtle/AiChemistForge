# Troubleshooting Guide

## Common Issues and Solutions

### Server Won't Start

**Symptoms:**
- Server fails to start
- Import errors
- Configuration errors

**Solutions:**

1. **Check Dependencies**
   ```bash
   uv sync --all-groups
   ```

2. **Check Configuration**
   ```bash
   # Verify .env file exists and is valid
   cat .env
   ```

3. **Check Python Version**
   ```bash
   python --version  # Should be 3.13+
   ```

4. **Check Logs**
   ```bash
   # Run with debug logging
   uv run unified-mcp-server --debug
   ```

### Tools Not Available

**Symptoms:**
- Tools not appearing in client
- Tool registration errors

**Solutions:**

1. **Check Tool Registration**
   ```python
   from unified_mcp_server.main import mcp
   print(list(mcp._tool_manager._tools.keys()))
   ```

2. **Check Tool Imports**
   ```bash
   # Verify tool modules can be imported
   python -c "from unified_mcp_server.tools.filesystem.file_tree_tool import register_file_tree_tool; print('OK')"
   ```

3. **Check FastMCP Version**
   ```bash
   uv pip list | grep fastmcp
   ```

### High Memory Usage

**Symptoms:**
- Memory usage grows over time
- Server becomes slow
- Out of memory errors

**Solutions:**

1. **Reduce Cache Size**
   ```bash
   CACHE_MAX_SIZE=500
   ```

2. **Reduce Cache TTL**
   ```bash
   CACHE_DEFAULT_TTL=60.0
   ```

3. **Limit Concurrent Operations**
   ```bash
   MAX_CONCURRENT_OPERATIONS=5
   ```

4. **Clear Cache Periodically**
   ```python
   from unified_mcp_server.utils.caching import cache_manager
   await cache_manager.clear()
   ```

### High CPU Usage

**Symptoms:**
- High CPU utilization
- Slow response times
- Server becomes unresponsive

**Solutions:**

1. **Reduce Concurrent Operations**
   ```bash
   MAX_CONCURRENT_OPERATIONS=5
   ```

2. **Enable Rate Limiting**
   ```bash
   RATE_LIMIT_ENABLED=true
   RATE_LIMIT_MAX_REQUESTS=50
   ```

3. **Optimize Tool Implementations**
   - Use async operations
   - Cache expensive computations
   - Batch operations

4. **Profile Performance**
   ```bash
   python -m cProfile -o profile.stats -m unified_mcp_server.main
   ```

### Timeout Errors

**Symptoms:**
- Operations timeout
- "Operation timed out" errors

**Solutions:**

1. **Increase Operation Timeout**
   ```bash
   OPERATION_TIMEOUT=60.0
   ```

2. **Check Tool Implementation**
   - Ensure tools use async operations
   - Avoid blocking operations
   - Optimize slow operations

3. **Check System Resources**
   - Monitor CPU and memory usage
   - Check disk I/O performance
   - Check network latency

### Rate Limiting Issues

**Symptoms:**
- "Rate limit exceeded" errors
- Requests rejected

**Solutions:**

1. **Adjust Rate Limit Settings**
   ```bash
   RATE_LIMIT_MAX_REQUESTS=200
   RATE_LIMIT_WINDOW_SECONDS=60.0
   ```

2. **Disable Rate Limiting (Development)**
   ```bash
   RATE_LIMIT_ENABLED=false
   ```

3. **Use Per-Tool Rate Limiting**
   ```bash
   RATE_LIMIT_PER_TOOL=true
   ```

### Metrics Not Collecting

**Symptoms:**
- No metrics available
- Metrics collector disabled

**Solutions:**

1. **Enable Metrics**
   ```bash
   METRICS_ENABLED=true
   ```

2. **Check Metrics Collector**
   ```python
   from unified_mcp_server.server.metrics import get_metrics_collector
   collector = get_metrics_collector()
   print(collector.is_enabled())
   ```

3. **Check Startup Hooks**
   ```python
   from unified_mcp_server.server.lifecycle import get_lifecycle_manager
   lifecycle = get_lifecycle_manager()
   print(lifecycle.get_startup_hooks_status())
   ```

### Tracing Not Working

**Symptoms:**
- No traces available
- Trace IDs not appearing in logs

**Solutions:**

1. **Enable Tracing**
   ```bash
   TRACING_ENABLED=true
   ```

2. **Check Tracer**
   ```python
   from unified_mcp_server.server.tracing import get_tracer
   tracer = get_tracer()
   print(tracer.enabled)
   ```

3. **Check Context Creation**
   ```python
   from unified_mcp_server.server.context import get_context_manager
   context_manager = get_context_manager()
   ctx = context_manager.create_request_context()
   ```

### Logging Issues

**Symptoms:**
- No logs appearing
- Logs in wrong format
- Missing correlation IDs

**Solutions:**

1. **Check Log Level**
   ```bash
   MCP_LOG_LEVEL=DEBUG
   ```

2. **Check Logging Configuration**
   ```python
   from unified_mcp_server.server.logging import setup_contextual_logging
   logger = setup_contextual_logging("mcp", "DEBUG")
   ```

3. **Verify Stdio Transport**
   - Logs go to stderr, not stdout
   - Check stderr output in client

### Connection Pool Exhaustion

**Symptoms:**
- "Pool exhausted" errors
- Timeout waiting for resources

**Solutions:**

1. **Increase Pool Size**
   ```python
   pool = resource_manager.register_pool(
       "my_pool",
       factory=create_resource,
       max_size=20,  # Increase from default
   )
   ```

2. **Check Resource Cleanup**
   - Ensure resources are released
   - Use async context managers
   - Check for resource leaks

3. **Reduce Pool Timeout**
   ```python
   pool = resource_manager.register_pool(
       "my_pool",
       factory=create_resource,
       timeout=10.0,  # Reduce timeout
   )
   ```

### Circuit Breaker Issues

**Symptoms:**
- Circuit breaker opens frequently
- Operations fail immediately

**Solutions:**

1. **Adjust Circuit Breaker Settings**
   ```python
   from unified_mcp_server.server.error_handling import CircuitBreaker

   breaker = CircuitBreaker(
       failure_threshold=10,  # Increase threshold
       recovery_timeout=120.0,  # Increase recovery time
   )
   ```

2. **Check Underlying Issues**
   - Fix root cause of failures
   - Improve error handling
   - Add retry logic

### Configuration Not Loading

**Symptoms:**
- Default values used instead of config
- Environment variables ignored

**Solutions:**

1. **Check .env File**
   ```bash
   # Verify .env file exists
   ls -la .env

   # Check file format
   cat .env
   ```

2. **Check Environment Variables**
   ```bash
   # Verify environment variables are set
   echo $MCP_LOG_LEVEL
   ```

3. **Check Config Loading**
   ```python
   from unified_mcp_server.server.config import load_config
   config = load_config()
   print(config.log_level)
   ```

## Debugging Techniques

### Enable Debug Logging

```bash
uv run unified-mcp-server --debug
```

### Check Server Status

```python
from unified_mcp_server.server.lifecycle import get_lifecycle_manager
from unified_mcp_server.server.metrics import get_metrics_collector

lifecycle = get_lifecycle_manager()
metrics = get_metrics_collector()

print("Health:", lifecycle.is_healthy())
print("Health Status:", lifecycle.get_health_status())
print("Metrics:", metrics.get_all_metrics())
```

### Inspect Middleware Chain

```python
from unified_mcp_server.server.middleware import get_middleware_chain

chain = get_middleware_chain()
print("Middleware:", [m.__class__.__name__ for m in chain.middlewares])
```

### Check Resource Pools

```python
from unified_mcp_server.server.resources import get_resource_manager

resource_manager = get_resource_manager()
print("Pools:", resource_manager.stats())
```

### Profile Performance

```bash
# CPU profiling
python -m cProfile -o profile.stats -m unified_mcp_server.main

# Analyze profile
python -m pstats profile.stats
```

## Getting Help

### Check Logs

Always check logs first:
- Server logs (stderr)
- Application logs
- System logs

### Collect Information

When reporting issues, include:
- Server version
- Python version
- Configuration (sanitized)
- Error messages
- Stack traces
- Relevant logs

### Common Debug Commands

```bash
# Check server startup
python -c "from unified_mcp_server.main import mcp; print('OK')"

# Check tool registration
python -c "from unified_mcp_server.main import mcp; print(list(mcp._tool_manager._tools.keys()))"

# Check configuration
python -c "from unified_mcp_server.server.config import load_config; print(load_config())"

# Check health
python -c "from unified_mcp_server.server.lifecycle import get_lifecycle_manager; print(get_lifecycle_manager().get_health_status())"
```

## Prevention

### Best Practices

1. **Monitor Metrics Regularly**
   - Set up alerts for key metrics
   - Review metrics dashboard
   - Track trends over time

2. **Test Configuration Changes**
   - Test in development first
   - Use environment profiles
   - Validate configuration

3. **Resource Management**
   - Use connection pools
   - Clean up resources properly
   - Monitor resource usage

4. **Error Handling**
   - Implement proper error handling
   - Use retry logic appropriately
   - Log errors with context

5. **Performance Testing**
   - Load test before deployment
   - Profile slow operations
   - Optimize hot paths



