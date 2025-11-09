# AiChemistForge MCP Server Architecture

## Overview

The AiChemistForge MCP server is built with FastMCP and follows MCP best practices for server lifecycle management, error handling, observability, and extensibility.

## Core Components

### 1. Server Lifecycle Management (`server/lifecycle.py`)

Manages server startup and shutdown with hook-based architecture:

- **LifecycleManager**: Coordinates startup/shutdown hooks
- **LifecycleHook**: Represents individual hooks with priority ordering
- **Health Checks**: Server health status and monitoring

**Key Features:**
- Priority-based hook execution
- Async hook support
- Health status tracking
- Graceful shutdown handling

### 2. Resource Management (`server/resources.py`)

Provides connection pooling and resource cleanup:

- **ResourcePool**: Generic resource pool with min/max size limits
- **ResourceManager**: Manages multiple resource pools
- **Async Context Managers**: Safe resource acquisition/release

**Key Features:**
- Connection pooling for external services
- Automatic resource cleanup
- Timeout handling
- Pool statistics

### 3. Error Handling (`server/error_handling.py`)

Comprehensive error handling framework:

- **Retry Logic**: Exponential backoff with jitter
- **Timeouts**: Operation timeout decorators
- **Circuit Breaker**: Prevents cascading failures
- **Graceful Degradation**: Fallback mechanisms

**Key Features:**
- Configurable retry strategies
- Circuit breaker pattern
- Structured error responses
- Error context propagation

### 4. Logging (`server/logging.py`)

Enhanced logging with correlation IDs and structured fields:

- **Contextual Logging**: Correlation ID propagation
- **Structured Fields**: Context-aware logging
- **Performance Timing**: Function execution timing
- **Stdio Compatibility**: MCP-compliant stderr logging

**Key Features:**
- Correlation ID tracking
- Context variables for async operations
- Performance timing decorators
- Structured log formatting

### 5. Metrics Collection (`server/metrics.py`)

Tool usage and server health metrics:

- **ToolMetrics**: Per-tool call tracking
- **MetricsCollector**: Aggregates all metrics
- **Server Health**: System resource monitoring
- **Percentiles**: P50, P95, P99 latency tracking

**Key Features:**
- Tool call counting and error tracking
- Latency percentiles
- Server health metrics (CPU, memory)
- Lightweight overhead

### 6. Request Tracing (`server/tracing.py`)

Request ID propagation and execution tracking:

- **Trace**: Complete request trace with spans
- **TraceSpan**: Individual operation spans
- **Tracer**: Manages trace lifecycle
- **Context Propagation**: Async context variables

**Key Features:**
- Request ID generation
- Span-based tracing
- Performance bottleneck identification
- Trace storage and retrieval

### 7. Context Management (`server/context.py`)

Server, request, and tool context propagation:

- **ServerContext**: Server-level metadata
- **RequestContext**: Per-request context
- **ToolContext**: Tool execution context
- **ContextManager**: Manages all contexts

**Key Features:**
- Context propagation through async chains
- Request ID tracking
- User context support
- Metadata attachment

### 8. Middleware System (`server/middleware.py`)

Request/response interception framework:

- **Middleware Protocol**: Standard middleware interface
- **RateLimitingMiddleware**: Request rate limiting
- **TimingMiddleware**: Request timing
- **MetricsMiddleware**: Automatic metrics collection
- **ValidationMiddleware**: Request validation

**Key Features:**
- Chain-based middleware execution
- Per-tool rate limiting
- Request/response interception
- Error handling integration

### 9. Configuration (`server/config.py`)

Centralized configuration management:

- **ServerConfig**: Pydantic-based configuration
- **Environment Variables**: .env file support
- **Performance Tuning**: Timeout, retry, cache settings
- **Monitoring**: Metrics and tracing configuration
- **Middleware**: Rate limiting and validation settings

**Key Features:**
- Type-safe configuration
- Environment-based profiles
- Comprehensive defaults
- Validation and error messages

### 10. Extensions API (`server/extensions.py`)

Plugin architecture for custom functionality:

- **Extension**: Extension container
- **ExtensionRegistry**: Extension management
- **Middleware Registration**: Custom middleware support
- **Hook Registration**: Startup/shutdown hooks

**Key Features:**
- Plugin discovery
- Extension activation
- Middleware integration
- Lifecycle hook support

## Data Flow

### Request Processing Flow

1. **Request Received**: FastMCP receives JSON-RPC request
2. **Context Creation**: Request context created with correlation ID
3. **Middleware Chain**: Request processed through middleware
   - Rate limiting check
   - Validation
   - Timing start
4. **Tool Execution**: Tool called with context
   - Metrics collection
   - Error handling
   - Tracing spans
5. **Response Processing**: Response processed through middleware (reverse order)
   - Timing end
   - Metrics recording
   - Response formatting
6. **Context Cleanup**: Request context cleared

### Startup Flow

1. **Configuration Load**: Load config from environment
2. **Component Initialization**: Initialize all server components
3. **Lifecycle Startup**: Execute startup hooks in priority order
   - Cache manager start
   - Resource pool initialization
   - Metrics enablement
4. **Tool Registration**: Register all MCP tools
5. **Server Ready**: Server ready to accept requests

### Shutdown Flow

1. **Signal Received**: SIGINT or SIGTERM received
2. **Lifecycle Shutdown**: Execute shutdown hooks (reverse priority)
   - Cache manager stop
   - Resource pool cleanup
3. **Context Cleanup**: Clear all contexts
4. **Graceful Exit**: Server exits cleanly

## Integration Points

### FastMCP Integration

The server integrates with FastMCP through:
- Tool registration via `@mcp.tool()` decorator
- Stdio transport (default)
- HTTP/SSE transport support
- JSON-RPC protocol handling

### Tool Integration

Tools integrate with server infrastructure through:
- Context management (request/tool context)
- Metrics collection (automatic via middleware)
- Error handling (retry, timeout decorators)
- Tracing (automatic span creation)

## Extension Points

### Custom Middleware

```python
from unified_mcp_server.server.middleware import Middleware

class CustomMiddleware:
    async def process_request(self, request):
        # Modify request
        return request

    async def process_response(self, request, response):
        # Modify response
        return response

    async def process_error(self, request, error):
        # Handle error
        return {"error": str(error)}
```

### Custom Extensions

```python
from unified_mcp_server.server.extensions import Extension, get_extension_registry

extension = Extension("my-extension", "1.0.0")
extension.register_middleware(CustomMiddleware())
extension.register_startup_hook(my_startup_hook, priority=50)
extension.activate()

registry = get_extension_registry()
registry.register(extension)
registry.activate_all()
```

## Performance Considerations

- **Async Operations**: All I/O operations are async
- **Connection Pooling**: Reuse connections for external services
- **Caching**: LRU cache with TTL for expensive operations
- **Concurrent Processing**: Semaphore-based concurrency limits
- **Metrics Overhead**: Lightweight metrics collection

## Security Considerations

- **Path Traversal Protection**: Input validation
- **Rate Limiting**: Prevent abuse
- **Error Sanitization**: Don't leak sensitive information
- **Context Isolation**: Per-request context isolation

## Monitoring and Observability

- **Metrics**: Tool usage, latency, errors
- **Tracing**: Request flow and performance
- **Logging**: Structured logs with correlation IDs
- **Health Checks**: Server health status

## Future Enhancements

- Authentication/authorization middleware
- Request queuing for high load
- Distributed tracing support
- Metrics export to Prometheus/StatsD
- WebSocket transport support



