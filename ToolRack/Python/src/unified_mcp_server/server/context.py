"""Context management system for the unified MCP server.

Provides server context, request context, and tool context injection
for propagating metadata and state across async operations.
"""

import contextvars
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .logging import get_correlation_id, set_correlation_id
from .tracing import get_tracer

logger = logging.getLogger("mcp.server.context")


@dataclass
class ServerContext:
    """Server-level context (shared across all requests)."""

    server_name: str
    start_time: float
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_uptime(self) -> float:
        """Get server uptime in seconds."""
        return time.time() - self.start_time


@dataclass
class RequestContext:
    """Request-level context (per-request)."""

    request_id: str
    correlation_id: str
    start_time: float
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_elapsed(self) -> float:
        """Get elapsed time since request start."""
        return time.time() - self.start_time


@dataclass
class ToolContext:
    """Tool execution context."""

    tool_name: str
    request_id: str
    start_time: float
    input_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_elapsed(self) -> float:
        """Get elapsed time since tool start."""
        return time.time() - self.start_time


# Context variables
server_context_var: contextvars.ContextVar[Optional[ServerContext]] = (
    contextvars.ContextVar("server_context", default=None)
)

request_context_var: contextvars.ContextVar[Optional[RequestContext]] = (
    contextvars.ContextVar("request_context", default=None)
)

tool_context_var: contextvars.ContextVar[Optional[ToolContext]] = (
    contextvars.ContextVar("tool_context", default=None)
)


class ContextManager:
    """Manages server, request, and tool contexts."""

    def __init__(self, server_name: str = "aichemist-forge", version: str = "1.0.0"):
        """Initialize the context manager.

        Args:
            server_name: Server name
            version: Server version
        """
        self.server_context = ServerContext(
            server_name=server_name,
            start_time=time.time(),
            version=version,
        )
        server_context_var.set(self.server_context)

    def get_server_context(self) -> ServerContext:
        """Get server context.

        Returns:
            ServerContext instance
        """
        ctx = server_context_var.get()
        if ctx is None:
            return self.server_context
        return ctx

    def create_request_context(
        self,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **metadata,
    ) -> RequestContext:
        """Create a new request context.

        Args:
            request_id: Optional request ID (generates one if None)
            correlation_id: Optional correlation ID (generates one if None)
            user_id: Optional user ID
            **metadata: Additional metadata

        Returns:
            RequestContext instance
        """
        if request_id is None:
            request_id = str(uuid.uuid4())[:8]

        if correlation_id is None:
            correlation_id = get_correlation_id() or set_correlation_id()

        ctx = RequestContext(
            request_id=request_id,
            correlation_id=correlation_id,
            start_time=time.time(),
            user_id=user_id,
            metadata=metadata,
        )

        request_context_var.set(ctx)
        set_correlation_id(correlation_id)

        # Start trace if tracing is enabled
        tracer = get_tracer()
        if tracer.enabled:
            tracer.start_trace(request_id=request_id, **metadata)

        logger.debug(f"Created request context: {request_id}")
        return ctx

    def get_request_context(self) -> Optional[RequestContext]:
        """Get current request context.

        Returns:
            RequestContext instance or None
        """
        return request_context_var.get()

    def clear_request_context(self) -> None:
        """Clear current request context."""
        ctx = request_context_var.get()
        if ctx:
            # End trace if tracing is enabled
            tracer = get_tracer()
            if tracer.enabled:
                tracer.end_trace()

        request_context_var.set(None)
        logger.debug("Cleared request context")

    def create_tool_context(
        self,
        tool_name: str,
        request_id: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        **metadata,
    ) -> ToolContext:
        """Create a new tool context.

        Args:
            tool_name: Tool name
            request_id: Optional request ID (uses current request if None)
            input_data: Optional input data
            **metadata: Additional metadata

        Returns:
            ToolContext instance
        """
        req_ctx = self.get_request_context()
        if request_id is None and req_ctx:
            request_id = req_ctx.request_id
        elif request_id is None:
            request_id = str(uuid.uuid4())[:8]

        ctx = ToolContext(
            tool_name=tool_name,
            request_id=request_id,
            start_time=time.time(),
            input_data=input_data or {},
            metadata=metadata,
        )

        tool_context_var.set(ctx)

        # Start span if tracing is enabled
        tracer = get_tracer()
        if tracer.enabled:
            tracer.start_span(
                tool_name,
                attributes={"input_data": input_data, **metadata},
            )

        logger.debug(f"Created tool context: {tool_name}")
        return ctx

    def get_tool_context(self) -> Optional[ToolContext]:
        """Get current tool context.

        Returns:
            ToolContext instance or None
        """
        return tool_context_var.get()

    def clear_tool_context(self) -> None:
        """Clear current tool context."""
        ctx = tool_context_var.get()
        if ctx:
            # End span if tracing is enabled
            tracer = get_tracer()
            if tracer.enabled:
                tracer.end_span()

        tool_context_var.set(None)
        logger.debug("Cleared tool context")

    def get_all_context(self) -> Dict[str, Any]:
        """Get all current context.

        Returns:
            Dictionary with all context information
        """
        return {
            "server": self.get_server_context().__dict__,
            "request": self.get_request_context().__dict__ if self.get_request_context() else None,
            "tool": self.get_tool_context().__dict__ if self.get_tool_context() else None,
        }


# Global context manager instance
_context_manager: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    """Get the global context manager instance.

    Returns:
        ContextManager instance
    """
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager


def get_current_request_id() -> Optional[str]:
    """Get current request ID.

    Returns:
        Request ID or None
    """
    ctx = request_context_var.get()
    return ctx.request_id if ctx else None


def get_current_tool_name() -> Optional[str]:
    """Get current tool name.

    Returns:
        Tool name or None
    """
    ctx = tool_context_var.get()
    return ctx.tool_name if ctx else None



