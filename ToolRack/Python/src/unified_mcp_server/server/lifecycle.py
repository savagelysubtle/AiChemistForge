"""Server lifecycle management for the unified MCP server.

Provides startup/shutdown hooks, health checks, and graceful resource cleanup
following MCP best practices for server lifecycle management.
"""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional

from ..utils.exceptions import ServerError

logger = logging.getLogger("mcp.server.lifecycle")


class LifecycleHook:
    """Represents a lifecycle hook with metadata."""

    def __init__(
        self,
        name: str,
        callback: Callable[[], Any],
        priority: int = 100,
        async_callback: bool = False,
    ):
        """Initialize a lifecycle hook.

        Args:
            name: Hook name for logging/debugging
            callback: Function to call during lifecycle event
            priority: Execution priority (lower = earlier execution)
            async_callback: Whether callback is async
        """
        self.name = name
        self.callback = callback
        self.priority = priority
        self.async_callback = async_callback
        self.executed = False
        self.execution_time: Optional[float] = None
        self.error: Optional[Exception] = None

    async def execute(self) -> None:
        """Execute the hook."""
        start_time = time.time()
        try:
            if self.async_callback:
                await self.callback()
            else:
                self.callback()
            self.executed = True
            self.execution_time = time.time() - start_time
            logger.debug(
                f"Lifecycle hook '{self.name}' executed successfully in {self.execution_time:.3f}s"
            )
        except Exception as e:
            self.error = e
            self.execution_time = time.time() - start_time
            logger.error(
                f"Lifecycle hook '{self.name}' failed after {self.execution_time:.3f}s: {e}",
                exc_info=True,
            )
            raise


class LifecycleManager:
    """Manages server lifecycle events (startup, shutdown, health checks)."""

    def __init__(self):
        """Initialize the lifecycle manager."""
        self._startup_hooks: List[LifecycleHook] = []
        self._shutdown_hooks: List[LifecycleHook] = []
        self._started = False
        self._shutting_down = False
        self._start_time: Optional[float] = None
        self._shutdown_time: Optional[float] = None

    def register_startup_hook(
        self,
        callback: Callable[[], Any],
        name: Optional[str] = None,
        priority: int = 100,
        async_callback: bool = False,
    ) -> None:
        """Register a startup hook.

        Args:
            callback: Function to call during startup
            name: Optional name for the hook (defaults to function name)
            priority: Execution priority (lower = earlier execution)
            async_callback: Whether callback is async
        """
        hook_name = name or getattr(callback, "__name__", "unnamed")
        hook = LifecycleHook(hook_name, callback, priority, async_callback)
        self._startup_hooks.append(hook)
        self._startup_hooks.sort(key=lambda h: h.priority)
        logger.debug(f"Registered startup hook '{hook_name}' with priority {priority}")

    def register_shutdown_hook(
        self,
        callback: Callable[[], Any],
        name: Optional[str] = None,
        priority: int = 100,
        async_callback: bool = False,
    ) -> None:
        """Register a shutdown hook.

        Args:
            callback: Function to call during shutdown
            name: Optional name for the hook (defaults to function name)
            priority: Execution priority (lower = earlier execution)
            async_callback: Whether callback is async
        """
        hook_name = name or getattr(callback, "__name__", "unnamed")
        hook = LifecycleHook(hook_name, callback, priority, async_callback)
        self._shutdown_hooks.append(hook)
        self._shutdown_hooks.sort(key=lambda h: h.priority)
        logger.debug(f"Registered shutdown hook '{hook_name}' with priority {priority}")

    async def startup(self) -> None:
        """Execute all startup hooks in priority order."""
        if self._started:
            logger.warning("Startup already executed, skipping")
            return

        logger.info("Starting server lifecycle...")
        self._start_time = time.time()

        for hook in self._startup_hooks:
            try:
                await hook.execute()
            except Exception as e:
                logger.critical(
                    f"Startup hook '{hook.name}' failed, continuing with other hooks: {e}"
                )
                # Continue with other hooks even if one fails
                # Critical hooks should raise exceptions themselves

        self._started = True
        startup_time = time.time() - self._start_time
        logger.info(
            f"Server lifecycle started successfully in {startup_time:.3f}s "
            f"({len(self._startup_hooks)} hooks executed)"
        )

    async def shutdown(self) -> None:
        """Execute all shutdown hooks in reverse priority order."""
        if self._shutting_down:
            logger.warning("Shutdown already in progress, skipping")
            return

        if not self._started:
            logger.warning("Shutdown called but server was never started")
            return

        logger.info("Shutting down server lifecycle...")
        self._shutting_down = True
        self._shutdown_time = time.time()

        # Execute shutdown hooks in reverse priority order
        for hook in reversed(self._shutdown_hooks):
            try:
                await hook.execute()
            except Exception as e:
                logger.error(
                    f"Shutdown hook '{hook.name}' failed, continuing with other hooks: {e}",
                    exc_info=True,
                )
                # Continue with other hooks even if one fails

        shutdown_time = time.time() - self._shutdown_time
        logger.info(
            f"Server lifecycle shutdown completed in {shutdown_time:.3f}s "
            f"({len(self._shutdown_hooks)} hooks executed)"
        )

    def is_healthy(self) -> bool:
        """Check if the server is healthy.

        Returns:
            True if server is healthy, False otherwise
        """
        if not self._started:
            return False
        if self._shutting_down:
            return False
        return True

    def get_health_status(self) -> Dict[str, Any]:
        """Get detailed health status.

        Returns:
            Dictionary with health status information
        """
        uptime = None
        if self._start_time:
            uptime = time.time() - self._start_time

        return {
            "healthy": self.is_healthy(),
            "started": self._started,
            "shutting_down": self._shutting_down,
            "uptime_seconds": uptime,
            "startup_hooks_count": len(self._startup_hooks),
            "shutdown_hooks_count": len(self._shutdown_hooks),
            "startup_hooks_executed": sum(1 for h in self._startup_hooks if h.executed),
            "startup_hooks_failed": sum(1 for h in self._startup_hooks if h.error is not None),
        }

    def get_startup_hooks_status(self) -> List[Dict[str, Any]]:
        """Get status of all startup hooks.

        Returns:
            List of hook status dictionaries
        """
        return [
            {
                "name": hook.name,
                "priority": hook.priority,
                "executed": hook.executed,
                "execution_time": hook.execution_time,
                "error": str(hook.error) if hook.error else None,
            }
            for hook in self._startup_hooks
        ]

    def get_shutdown_hooks_status(self) -> List[Dict[str, Any]]:
        """Get status of all shutdown hooks.

        Returns:
            List of hook status dictionaries
        """
        return [
            {
                "name": hook.name,
                "priority": hook.priority,
                "executed": hook.executed,
                "execution_time": hook.execution_time,
                "error": str(hook.error) if hook.error else None,
            }
            for hook in self._shutdown_hooks
        ]


# Global lifecycle manager instance
_lifecycle_manager: Optional[LifecycleManager] = None


def get_lifecycle_manager() -> LifecycleManager:
    """Get the global lifecycle manager instance.

    Returns:
        LifecycleManager instance
    """
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = LifecycleManager()
    return _lifecycle_manager


def register_startup_hook(
    callback: Callable[[], Any],
    name: Optional[str] = None,
    priority: int = 100,
    async_callback: bool = False,
) -> None:
    """Convenience function to register a startup hook.

    Args:
        callback: Function to call during startup
        name: Optional name for the hook
        priority: Execution priority
        async_callback: Whether callback is async
    """
    get_lifecycle_manager().register_startup_hook(callback, name, priority, async_callback)


def register_shutdown_hook(
    callback: Callable[[], Any],
    name: Optional[str] = None,
    priority: int = 100,
    async_callback: bool = False,
) -> None:
    """Convenience function to register a shutdown hook.

    Args:
        callback: Function to call during shutdown
        name: Optional name for the hook
        priority: Execution priority
        async_callback: Whether callback is async
    """
    get_lifecycle_manager().register_shutdown_hook(callback, name, priority, async_callback)



