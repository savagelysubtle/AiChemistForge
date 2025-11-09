"""Metrics collection system for the unified MCP server.

Tracks tool usage, latency, errors, and server health metrics
following MCP best practices for observability.
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger("mcp.server.metrics")


@dataclass
class ToolMetrics:
    """Metrics for a single tool."""

    name: str
    call_count: int = 0
    error_count: int = 0
    total_latency: float = 0.0
    min_latency: Optional[float] = None
    max_latency: Optional[float] = None
    recent_latencies: deque = field(default_factory=lambda: deque(maxlen=100))

    def record_call(self, latency: float, error: bool = False) -> None:
        """Record a tool call.

        Args:
            latency: Call latency in seconds
            error: Whether the call resulted in an error
        """
        self.call_count += 1
        if error:
            self.error_count += 1
        else:
            self.total_latency += latency
            self.recent_latencies.append(latency)

            if self.min_latency is None or latency < self.min_latency:
                self.min_latency = latency
            if self.max_latency is None or latency > self.max_latency:
                self.max_latency = latency

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for this tool.

        Returns:
            Dictionary with tool statistics
        """
        stats = {
            "name": self.name,
            "call_count": self.call_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / self.call_count if self.call_count > 0 else 0.0,
        }

        if self.call_count > self.error_count:
            avg_latency = self.total_latency / (self.call_count - self.error_count)
            stats["avg_latency"] = avg_latency
            stats["min_latency"] = self.min_latency
            stats["max_latency"] = self.max_latency

            # Calculate percentiles from recent latencies
            if self.recent_latencies:
                sorted_latencies = sorted(self.recent_latencies)
                n = len(sorted_latencies)
                stats["p50_latency"] = sorted_latencies[n // 2]
                stats["p95_latency"] = sorted_latencies[int(n * 0.95)]
                stats["p99_latency"] = sorted_latencies[int(n * 0.99)]
        else:
            stats["avg_latency"] = None
            stats["min_latency"] = None
            stats["max_latency"] = None

        return stats


class MetricsCollector:
    """Collects and aggregates metrics for the MCP server."""

    def __init__(self):
        """Initialize the metrics collector."""
        self._tool_metrics: Dict[str, ToolMetrics] = {}
        self._start_time = time.time()
        self._lock = asyncio.Lock()
        self._enabled = True

    def enable(self) -> None:
        """Enable metrics collection."""
        self._enabled = True
        logger.info("Metrics collection enabled")

    def disable(self) -> None:
        """Disable metrics collection."""
        self._enabled = False
        logger.info("Metrics collection disabled")

    def is_enabled(self) -> bool:
        """Check if metrics collection is enabled.

        Returns:
            True if enabled, False otherwise
        """
        return self._enabled

    async def record_tool_call(
        self, tool_name: str, latency: float, error: bool = False
    ) -> None:
        """Record a tool call.

        Args:
            tool_name: Name of the tool
            latency: Call latency in seconds
            error: Whether the call resulted in an error
        """
        if not self._enabled:
            return

        async with self._lock:
            if tool_name not in self._tool_metrics:
                self._tool_metrics[tool_name] = ToolMetrics(name=tool_name)
            self._tool_metrics[tool_name].record_call(latency, error)

    def get_tool_metrics(self, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for a specific tool or all tools.

        Args:
            tool_name: Optional tool name (None for all tools)

        Returns:
            Dictionary with tool metrics
        """
        if tool_name:
            if tool_name in self._tool_metrics:
                return self._tool_metrics[tool_name].get_stats()
            return {}

        return {
            name: metrics.get_stats()
            for name, metrics in self._tool_metrics.items()
        }

    def get_server_health(self) -> Dict[str, Any]:
        """Get server health metrics.

        Returns:
            Dictionary with server health information
        """
        uptime = time.time() - self._start_time

        # Calculate total tool calls
        total_calls = sum(m.call_count for m in self._tool_metrics.values())
        total_errors = sum(m.error_count for m in self._tool_metrics.values())

        health = {
            "uptime_seconds": uptime,
            "total_tool_calls": total_calls,
            "total_tool_errors": total_errors,
            "error_rate": total_errors / total_calls if total_calls > 0 else 0.0,
            "tools_tracked": len(self._tool_metrics),
        }

        # Add system metrics if psutil is available
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process()
                memory_info = process.memory_info()
                cpu_percent = process.cpu_percent(interval=0.1)

                health.update({
                    "memory_rss_mb": memory_info.rss / 1024 / 1024,
                    "memory_vms_mb": memory_info.vms / 1024 / 1024,
                    "cpu_percent": cpu_percent,
                })
            except Exception as e:
                logger.warning(f"Error collecting system metrics: {e}")
                health["system_metrics_error"] = str(e)

        return health

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics.

        Returns:
            Dictionary with all metrics
        """
        return {
            "server_health": self.get_server_health(),
            "tool_metrics": self.get_tool_metrics(),
        }

    def reset(self) -> None:
        """Reset all metrics."""
        async def _reset():
            async with self._lock:
                self._tool_metrics.clear()
                self._start_time = time.time()
                logger.info("Metrics reset")

        # Run synchronously if possible
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(_reset())
            else:
                loop.run_until_complete(_reset())
        except RuntimeError:
            # No event loop, reset synchronously
            self._tool_metrics.clear()
            self._start_time = time.time()
            logger.info("Metrics reset")


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance.

    Returns:
        MetricsCollector instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def record_tool_call(tool_name: str, latency: float, error: bool = False) -> None:
    """Convenience function to record a tool call.

    Args:
        tool_name: Name of the tool
        latency: Call latency in seconds
        error: Whether the call resulted in an error
    """
    collector = get_metrics_collector()
    if collector.is_enabled():
        # Try to record asynchronously
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(
                    collector.record_tool_call(tool_name, latency, error)
                )
            else:
                loop.run_until_complete(
                    collector.record_tool_call(tool_name, latency, error)
                )
        except RuntimeError:
            # No event loop, create one
            asyncio.run(collector.record_tool_call(tool_name, latency, error))


def timed_tool_call(tool_name: str):
    """Decorator for timing tool calls and recording metrics.

    Args:
        tool_name: Name of the tool

    Returns:
        Decorated function
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            error = False
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception:
                error = True
                raise
            finally:
                latency = time.time() - start_time
                record_tool_call(tool_name, latency, error)

        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            error = False
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                error = True
                raise
            finally:
                latency = time.time() - start_time
                record_tool_call(tool_name, latency, error)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator

