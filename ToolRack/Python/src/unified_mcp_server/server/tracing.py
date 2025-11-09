"""Request tracing system for the unified MCP server.

Provides request ID generation, propagation, and execution tracking
for debugging and performance analysis.
"""

import asyncio
import contextvars
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .logging import get_correlation_id, set_correlation_id

logger = logging.getLogger("mcp.server.tracing")


@dataclass
class TraceSpan:
    """Represents a single span in a trace."""

    name: str
    start_time: float
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    children: List["TraceSpan"] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def duration(self) -> Optional[float]:
        """Get span duration in seconds."""
        if self.end_time is None:
            return None
        return self.end_time - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary."""
        return {
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "attributes": self.attributes,
            "children": [child.to_dict() for child in self.children],
            "error": self.error,
        }


@dataclass
class Trace:
    """Represents a complete trace with multiple spans."""

    trace_id: str
    request_id: str
    start_time: float
    end_time: Optional[float] = None
    root_span: Optional[TraceSpan] = None
    attributes: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> Optional[float]:
        """Get trace duration in seconds."""
        if self.end_time is None:
            return None
        return self.end_time - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary."""
        return {
            "trace_id": self.trace_id,
            "request_id": self.request_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "attributes": self.attributes,
            "root_span": self.root_span.to_dict() if self.root_span else None,
        }


# Context variables for tracing
current_trace: contextvars.ContextVar[Optional[Trace]] = contextvars.ContextVar(
    "current_trace", default=None
)

current_span: contextvars.ContextVar[Optional[TraceSpan]] = contextvars.ContextVar(
    "current_span", default=None
)


class Tracer:
    """Tracer for creating and managing traces."""

    def __init__(self, enabled: bool = True):
        """Initialize the tracer.

        Args:
            enabled: Whether tracing is enabled
        """
        self.enabled = enabled
        self._traces: List[Trace] = []
        self._max_traces = 1000  # Keep last 1000 traces
        self._lock = asyncio.Lock()

    def start_trace(
        self, request_id: Optional[str] = None, **attributes
    ) -> Trace:
        """Start a new trace.

        Args:
            request_id: Optional request ID (generates one if None)
            **attributes: Additional trace attributes

        Returns:
            Trace object
        """
        if not self.enabled:
            return Trace(
                trace_id="",
                request_id=request_id or "",
                start_time=time.time(),
            )

        trace_id = str(uuid.uuid4())
        if request_id is None:
            request_id = str(uuid.uuid4())[:8]

        trace = Trace(
            trace_id=trace_id,
            request_id=request_id,
            start_time=time.time(),
            attributes=attributes,
        )

        current_trace.set(trace)
        set_correlation_id(request_id)

        logger.debug(f"Started trace {trace_id} for request {request_id}")
        return trace

    def end_trace(self, trace: Optional[Trace] = None) -> None:
        """End a trace.

        Args:
            trace: Optional trace to end (uses current if None)
        """
        if not self.enabled:
            return

        if trace is None:
            trace = current_trace.get()

        if trace is None:
            return

        trace.end_time = time.time()

        # Store trace (with size limit)
        asyncio.create_task(self._store_trace(trace))

        # Clear context
        current_trace.set(None)
        current_span.set(None)

        logger.debug(
            f"Ended trace {trace.trace_id} (duration: {trace.duration:.3f}s)"
        )

    async def _store_trace(self, trace: Trace) -> None:
        """Store a trace (with size limit).

        Args:
            trace: Trace to store
        """
        async with self._lock:
            self._traces.append(trace)
            if len(self._traces) > self._max_traces:
                self._traces.pop(0)

    def start_span(
        self, name: str, parent: Optional[TraceSpan] = None, **attributes
    ) -> TraceSpan:
        """Start a new span.

        Args:
            name: Span name
            parent: Optional parent span
            **attributes: Additional span attributes

        Returns:
            TraceSpan object
        """
        if not self.enabled:
            return TraceSpan(name=name, start_time=time.time())

        span = TraceSpan(name=name, start_time=time.time(), attributes=attributes)

        trace = current_trace.get()
        if trace is None:
            # Create a trace if none exists
            trace = self.start_trace()

        if parent is None:
            parent = current_span.get()

        if parent is None:
            # This is the root span
            trace.root_span = span
        else:
            parent.children.append(span)

        current_span.set(span)
        logger.debug(f"Started span '{name}'")
        return span

    def end_span(self, span: Optional[TraceSpan] = None, error: Optional[str] = None) -> None:
        """End a span.

        Args:
            span: Optional span to end (uses current if None)
            error: Optional error message
        """
        if not self.enabled:
            return

        if span is None:
            span = current_span.get()

        if span is None:
            return

        span.end_time = time.time()
        if error:
            span.error = error

        # Move to parent span
        trace = current_trace.get()
        if trace and trace.root_span:
            # Find parent by traversing the tree
            def find_parent(node: TraceSpan, target: TraceSpan) -> Optional[TraceSpan]:
                if target in node.children:
                    return node
                for child in node.children:
                    parent = find_parent(child, target)
                    if parent:
                        return parent
                return None

            if span != trace.root_span:
                parent = find_parent(trace.root_span, span)
                if parent:
                    current_span.set(parent)
                else:
                    current_span.set(None)
            else:
                current_span.set(None)

        logger.debug(
            f"Ended span '{span.name}' (duration: {span.duration:.3f}s)"
            + (f" with error: {error}" if error else "")
        )

    def get_trace(self, trace_id: Optional[str] = None) -> Optional[Trace]:
        """Get a trace by ID or current trace.

        Args:
            trace_id: Optional trace ID (uses current if None)

        Returns:
            Trace object or None
        """
        if trace_id is None:
            return current_trace.get()

        for trace in self._traces:
            if trace.trace_id == trace_id:
                return trace

        return None

    def get_recent_traces(self, limit: int = 10) -> List[Trace]:
        """Get recent traces.

        Args:
            limit: Maximum number of traces to return

        Returns:
            List of traces
        """
        return self._traces[-limit:]

    def clear_traces(self) -> None:
        """Clear all stored traces."""
        self._traces.clear()
        logger.info("Cleared all traces")


# Global tracer instance
_tracer: Optional[Tracer] = None


def get_tracer() -> Tracer:
    """Get the global tracer instance.

    Returns:
        Tracer instance
    """
    global _tracer
    if _tracer is None:
        _tracer = Tracer()
    return _tracer


def trace_function(name: Optional[str] = None):
    """Decorator for tracing function execution.

    Args:
        name: Optional span name (defaults to function name)

    Returns:
        Decorated function
    """
    def decorator(func):
        span_name = name or func.__name__

        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            if not tracer.enabled:
                return await func(*args, **kwargs)

            span = tracer.start_span(
                span_name,
                attributes={"function": func.__name__, "module": func.__module__},
            )
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                tracer.end_span(span, error=str(e))
                raise
            finally:
                tracer.end_span(span)

        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            if not tracer.enabled:
                return func(*args, **kwargs)

            span = tracer.start_span(
                span_name,
                attributes={"function": func.__name__, "module": func.__module__},
            )
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                tracer.end_span(span, error=str(e))
                raise
            finally:
                tracer.end_span(span)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator



