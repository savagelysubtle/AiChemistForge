"""Resource pool management for the unified MCP server.

Provides async context managers for shared resources, connection pooling,
and efficient resource cleanup following MCP best practices.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, Generic, Optional, TypeVar, Union

from ..utils.exceptions import ResourceError

logger = logging.getLogger("mcp.server.resources")

T = TypeVar("T")


class ResourcePool(Generic[T]):
    """Generic resource pool for managing shared resources."""

    def __init__(
        self,
        factory: Callable[[], T],
        max_size: int = 10,
        min_size: int = 1,
        timeout: float = 30.0,
        cleanup_func: Optional[Callable[[T], Any]] = None,
    ):
        """Initialize a resource pool.

        Args:
            factory: Function to create new resources
            max_size: Maximum pool size
            min_size: Minimum pool size (pre-allocated)
            timeout: Timeout for acquiring resources (seconds)
            cleanup_func: Optional function to clean up resources
        """
        self.factory = factory
        self.max_size = max_size
        self.min_size = min_size
        self.timeout = timeout
        self.cleanup_func = cleanup_func

        self._pool: asyncio.Queue[Optional[T]] = asyncio.Queue(maxsize=max_size)
        self._created_count = 0
        self._active_count = 0
        self._lock = asyncio.Lock()
        self._closed = False

    async def initialize(self) -> None:
        """Initialize the pool with minimum resources."""
        async with self._lock:
            if self._closed:
                raise ResourceError("Pool is closed")

            for _ in range(self.min_size):
                resource = self.factory()
                await self._pool.put(resource)
                self._created_count += 1

            logger.debug(
                f"Resource pool initialized with {self.min_size} resources "
                f"(max: {self.max_size})"
            )

    async def acquire(self) -> T:
        """Acquire a resource from the pool.

        Returns:
            Resource from the pool

        Raises:
            ResourceError: If pool is closed or timeout exceeded
        """
        if self._closed:
            raise ResourceError("Pool is closed")

        try:
            # Try to get from pool with timeout
            resource = await asyncio.wait_for(self._pool.get(), timeout=self.timeout)
        except asyncio.TimeoutError:
            raise ResourceError(f"Timeout waiting for resource (>{self.timeout}s)")

        # If we got None (sentinel), create a new resource
        if resource is None:
            async with self._lock:
                if self._created_count < self.max_size:
                    resource = self.factory()
                    self._created_count += 1
                    logger.debug(f"Created new resource (total: {self._created_count})")
                else:
                    # Put None back and wait again
                    await self._pool.put(None)
                    try:
                        resource = await asyncio.wait_for(
                            self._pool.get(), timeout=self.timeout
                        )
                    except asyncio.TimeoutError:
                        raise ResourceError(
                            f"Pool exhausted and timeout exceeded (>{self.timeout}s)"
                        )

        async with self._lock:
            self._active_count += 1

        return resource

    async def release(self, resource: T) -> None:
        """Release a resource back to the pool.

        Args:
            resource: Resource to release
        """
        if self._closed:
            # Pool is closed, clean up the resource
            if self.cleanup_func:
                try:
                    if asyncio.iscoroutinefunction(self.cleanup_func):
                        await self.cleanup_func(resource)
                    else:
                        self.cleanup_func(resource)
                except Exception as e:
                    logger.error(f"Error cleaning up resource: {e}", exc_info=True)
            return

        async with self._lock:
            self._active_count -= 1

        try:
            await self._pool.put(resource)
        except Exception as e:
            logger.error(f"Error releasing resource to pool: {e}", exc_info=True)

    async def close(self) -> None:
        """Close the pool and clean up all resources."""
        async with self._lock:
            if self._closed:
                return

            self._closed = True

            # Clean up all resources in the pool
            cleaned = 0
            while not self._pool.empty():
                try:
                    resource = await asyncio.wait_for(self._pool.get(), timeout=0.1)
                    if resource is not None and self.cleanup_func:
                        try:
                            if asyncio.iscoroutinefunction(self.cleanup_func):
                                await self.cleanup_func(resource)
                            else:
                                self.cleanup_func(resource)
                        except Exception as e:
                            logger.error(f"Error cleaning up resource: {e}", exc_info=True)
                    cleaned += 1
                except asyncio.TimeoutError:
                    break

            logger.debug(f"Resource pool closed, cleaned up {cleaned} resources")

    @asynccontextmanager
    async def acquire_context(self):
        """Async context manager for acquiring and releasing resources.

        Usage:
            async with pool.acquire_context() as resource:
                # Use resource
                pass
        """
        resource = await self.acquire()
        try:
            yield resource
        finally:
            await self.release(resource)

    def stats(self) -> Dict[str, Any]:
        """Get pool statistics.

        Returns:
            Dictionary with pool statistics
        """
        return {
            "max_size": self.max_size,
            "min_size": self.min_size,
            "created_count": self._created_count,
            "active_count": self._active_count,
            "available_count": self._pool.qsize(),
            "closed": self._closed,
        }


class ResourceManager:
    """Manages multiple resource pools."""

    def __init__(self):
        """Initialize the resource manager."""
        self._pools: Dict[str, ResourcePool] = {}
        self._initialized = False

    def register_pool(
        self,
        name: str,
        factory: Callable[[], T],
        max_size: int = 10,
        min_size: int = 1,
        timeout: float = 30.0,
        cleanup_func: Optional[Callable[[T], Any]] = None,
    ) -> ResourcePool[T]:
        """Register a new resource pool.

        Args:
            name: Pool name
            factory: Function to create new resources
            max_size: Maximum pool size
            min_size: Minimum pool size
            timeout: Timeout for acquiring resources
            cleanup_func: Optional cleanup function

        Returns:
            Created ResourcePool instance
        """
        if name in self._pools:
            raise ResourceError(f"Pool '{name}' already registered")

        pool = ResourcePool(factory, max_size, min_size, timeout, cleanup_func)
        self._pools[name] = pool
        logger.debug(f"Registered resource pool '{name}'")
        return pool

    def get_pool(self, name: str) -> ResourcePool:
        """Get a resource pool by name.

        Args:
            name: Pool name

        Returns:
            ResourcePool instance

        Raises:
            ResourceError: If pool not found
        """
        if name not in self._pools:
            raise ResourceError(f"Pool '{name}' not found")
        return self._pools[name]

    async def initialize_all(self) -> None:
        """Initialize all registered pools."""
        if self._initialized:
            logger.warning("Resource manager already initialized")
            return

        logger.info(f"Initializing {len(self._pools)} resource pools...")
        for name, pool in self._pools.items():
            try:
                await pool.initialize()
                logger.debug(f"Initialized resource pool '{name}'")
            except Exception as e:
                logger.error(f"Failed to initialize pool '{name}': {e}", exc_info=True)
                raise

        self._initialized = True
        logger.info("All resource pools initialized successfully")

    async def close_all(self) -> None:
        """Close all resource pools."""
        if not self._initialized:
            logger.warning("Resource manager not initialized, skipping close")
            return

        logger.info(f"Closing {len(self._pools)} resource pools...")
        for name, pool in self._pools.items():
            try:
                await pool.close()
                logger.debug(f"Closed resource pool '{name}'")
            except Exception as e:
                logger.error(f"Error closing pool '{name}': {e}", exc_info=True)

        self._initialized = False
        logger.info("All resource pools closed successfully")

    def stats(self) -> Dict[str, Any]:
        """Get statistics for all pools.

        Returns:
            Dictionary with pool statistics
        """
        return {
            "initialized": self._initialized,
            "pools": {name: pool.stats() for name, pool in self._pools.items()},
        }


# Global resource manager instance
_resource_manager: Optional[ResourceManager] = None


def get_resource_manager() -> ResourceManager:
    """Get the global resource manager instance.

    Returns:
        ResourceManager instance
    """
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager



