# Monitoring and Observability Guide

## Overview

The AiChemistForge MCP server provides comprehensive monitoring and observability through metrics, tracing, and structured logging.

## Metrics Collection

### Enabling Metrics

Metrics are enabled by default. Configure via environment variable:

```bash
METRICS_ENABLED=true
```

### Tool Metrics

Track per-tool performance:

```python
from unified_mcp_server.server.metrics import get_metrics_collector

collector = get_metrics_collector()
tool_metrics = collector.get_tool_metrics("tool_name")

# Returns:
# {
#     "name": "tool_name",
#     "call_count": 100,
#     "error_count": 2,
#     "error_rate": 0.02,
#     "avg_latency": 0.150,
#     "min_latency": 0.050,
#     "max_latency": 0.500,
#     "p50_latency": 0.120,
#     "p95_latency": 0.300,
#     "p99_latency": 0.450
# }
```

### Server Health Metrics

Monitor server health:

```python
server_health = collector.get_server_health()

# Returns:
# {
#     "uptime_seconds": 3600.0,
#     "memory_rss_mb": 150.5,
#     "memory_vms_mb": 200.0,
#     "cpu_percent": 25.5,
#     "total_tool_calls": 1000,
#     "total_tool_errors": 5,
#     "error_rate": 0.005,
#     "tools_tracked": 6
# }
```

### All Metrics

Get comprehensive metrics:

```python
all_metrics = collector.get_all_metrics()
```

## Request Tracing

### Enabling Tracing

Tracing is enabled by default:

```bash
TRACING_ENABLED=true
```

### Trace Structure

Traces consist of:
- **Trace ID**: Unique identifier for the trace
- **Request ID**: Correlation ID for the request
- **Spans**: Individual operations within the trace
- **Attributes**: Metadata attached to spans

### Accessing Traces

```python
from unified_mcp_server.server.tracing import get_tracer

tracer = get_tracer()

# Get current trace
trace = tracer.get_trace()

# Get trace by ID
trace = tracer.get_trace("trace-id")

# Get recent traces
recent_traces = tracer.get_recent_traces(limit=10)
```

### Trace Function Decorator

Automatically trace function execution:

```python
from unified_mcp_server.server.tracing import trace_function

@trace_function(name="my_operation")
async def my_function():
    # Function implementation
    pass
```

## Structured Logging

### Correlation IDs

Logs automatically include correlation IDs:

```python
from unified_mcp_server.server.logging import set_correlation_id, get_correlation_id

# Set correlation ID
corr_id = set_correlation_id()

# Get current correlation ID
current_id = get_correlation_id()
```

### Log Context

Add context to logs:

```python
from unified_mcp_server.server.logging import add_log_context, log_context_manager

# Add persistent context
add_log_context("user_id", "12345")

# Add temporary context
with log_context_manager(request_id="abc", tool_name="my_tool"):
    logger.info("This log includes request_id and tool_name")
```

### Performance Timing

Time function execution:

```python
from unified_mcp_server.server.logging import timed

@timed(log_args=True, log_result=False)
async def my_function(param: str):
    # Function implementation
    pass
```

## Health Checks

### Server Health Status

Check server health:

```python
from unified_mcp_server.server.lifecycle import get_lifecycle_manager

lifecycle = get_lifecycle_manager()
is_healthy = lifecycle.is_healthy()
health_status = lifecycle.get_health_status()
```

### Health Status Fields

- `healthy`: Boolean indicating if server is healthy
- `started`: Whether server has started
- `shutting_down`: Whether server is shutting down
- `uptime_seconds`: Server uptime
- `startup_hooks_count`: Number of startup hooks
- `shutdown_hooks_count`: Number of shutdown hooks
- `startup_hooks_executed`: Number of executed startup hooks
- `startup_hooks_failed`: Number of failed startup hooks

## Monitoring Best Practices

### 1. Enable All Observability Features

```bash
METRICS_ENABLED=true
TRACING_ENABLED=true
HEALTH_CHECK_ENABLED=true
```

### 2. Monitor Key Metrics

- Tool call counts and error rates
- Latency percentiles (P50, P95, P99)
- Server resource usage (CPU, memory)
- Error rates and patterns

### 3. Set Up Alerts

Monitor for:
- High error rates (> 1%)
- High latency (P95 > 1s)
- High memory usage (> 80%)
- High CPU usage (> 80%)

### 4. Use Correlation IDs

Always include correlation IDs in logs for request tracing.

### 5. Log Structured Data

Use structured logging with context for better searchability.

## Exporting Metrics

### Custom Export

Create custom metric exporters:

```python
from unified_mcp_server.server.metrics import get_metrics_collector

async def export_metrics():
    collector = get_metrics_collector()
    metrics = collector.get_all_metrics()

    # Export to Prometheus, StatsD, etc.
    # prometheus_client.gauge('tool_calls').set(metrics['tool_metrics']['call_count'])
```

### Periodic Export

Set up periodic metric export:

```python
import asyncio

async def periodic_export(interval: float = 60.0):
    while True:
        await export_metrics()
        await asyncio.sleep(interval)

# Start export task
asyncio.create_task(periodic_export())
```

## Log Aggregation

### Structured Log Format

Logs follow structured format:

```
[correlation_id] context | timestamp [level] logger: message
```

### Log Levels

- **DEBUG**: Detailed debugging information
- **INFO**: General informational messages
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **CRITICAL**: Critical errors

### Log Filtering

Filter logs by:
- Correlation ID
- Log level
- Logger name
- Context fields

## Performance Monitoring

### Track Slow Operations

Use timing decorators to identify slow operations:

```python
@timed(level=logging.WARNING)
async def potentially_slow_operation():
    # Operation that should complete quickly
    pass
```

### Monitor Resource Usage

Track server resource usage:

```python
health = lifecycle.get_health_status()
metrics = collector.get_server_health()

# Monitor memory usage
memory_mb = metrics.get("memory_rss_mb", 0)
if memory_mb > 500:
    logger.warning(f"High memory usage: {memory_mb}MB")

# Monitor CPU usage
cpu_percent = metrics.get("cpu_percent", 0)
if cpu_percent > 80:
    logger.warning(f"High CPU usage: {cpu_percent}%")
```

## Troubleshooting with Monitoring

### High Error Rate

1. Check error logs for patterns
2. Review tool metrics for specific failing tools
3. Check server health status
4. Review recent traces for error patterns

### High Latency

1. Check latency percentiles (P95, P99)
2. Identify slow tools via metrics
3. Review traces for bottlenecks
4. Check server resource usage

### Memory Leaks

1. Monitor memory usage over time
2. Check cache sizes
3. Review resource pool usage
4. Check for unclosed connections

## Integration with External Systems

### Prometheus

Export metrics to Prometheus:

```python
from prometheus_client import Counter, Histogram

tool_calls = Counter('mcp_tool_calls_total', 'Total tool calls', ['tool'])
tool_latency = Histogram('mcp_tool_latency_seconds', 'Tool latency', ['tool'])

# Update Prometheus metrics from collector
metrics = collector.get_tool_metrics()
for tool_name, tool_metrics in metrics.items():
    tool_calls.labels(tool=tool_name).inc(tool_metrics['call_count'])
```

### StatsD

Export metrics to StatsD:

```python
from statsd import StatsClient

statsd = StatsClient()

# Export metrics
metrics = collector.get_tool_metrics()
for tool_name, tool_metrics in metrics.items():
    statsd.gauge(f'tool.{tool_name}.calls', tool_metrics['call_count'])
    statsd.timing(f'tool.{tool_name}.latency', tool_metrics['avg_latency'] * 1000)
```

### Log Aggregation Services

Send logs to services like:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Splunk
- Datadog
- CloudWatch

Configure log handlers to send to these services while maintaining stderr output for MCP compatibility.



