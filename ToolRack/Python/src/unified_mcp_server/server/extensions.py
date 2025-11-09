"""Server extension API for the unified MCP server.

Provides plugin architecture for custom middleware and hook registration
following MCP best practices for extensibility.
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from .lifecycle import get_lifecycle_manager
from .middleware import Middleware, MiddlewareChain, get_middleware_chain

logger = logging.getLogger("mcp.server.extensions")


class Extension:
    """Represents a server extension."""

    def __init__(self, name: str, version: str = "1.0.0"):
        """Initialize an extension.

        Args:
            name: Extension name
            version: Extension version
        """
        self.name = name
        self.version = version
        self.middleware: List[Middleware] = []
        self.startup_hooks: List[Callable[[], Any]] = []
        self.shutdown_hooks: List[Callable[[], Any]] = []

    def register_middleware(self, middleware: Middleware) -> None:
        """Register middleware for this extension.

        Args:
            middleware: Middleware instance
        """
        self.middleware.append(middleware)
        logger.debug(f"Extension '{self.name}' registered middleware: {middleware.__class__.__name__}")

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
            name: Optional hook name
            priority: Execution priority
            async_callback: Whether callback is async
        """
        lifecycle_manager = get_lifecycle_manager()
        lifecycle_manager.register_startup_hook(callback, name, priority, async_callback)
        self.startup_hooks.append(callback)
        logger.debug(f"Extension '{self.name}' registered startup hook: {name or callback.__name__}")

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
            name: Optional hook name
            priority: Execution priority
            async_callback: Whether callback is async
        """
        lifecycle_manager = get_lifecycle_manager()
        lifecycle_manager.register_shutdown_hook(callback, name, priority, async_callback)
        self.shutdown_hooks.append(callback)
        logger.debug(f"Extension '{self.name}' registered shutdown hook: {name or callback.__name__}")

    def activate(self) -> None:
        """Activate the extension by registering middleware."""
        middleware_chain = get_middleware_chain()
        for middleware in self.middleware:
            middleware_chain.add(middleware)
        logger.info(f"Extension '{self.name}' v{self.version} activated")


class ExtensionRegistry:
    """Registry for managing server extensions."""

    def __init__(self):
        """Initialize the extension registry."""
        self.extensions: Dict[str, Extension] = {}

    def register(self, extension: Extension) -> None:
        """Register an extension.

        Args:
            extension: Extension instance

        Raises:
            ValueError: If extension with same name already registered
        """
        if extension.name in self.extensions:
            raise ValueError(f"Extension '{extension.name}' already registered")
        self.extensions[extension.name] = extension
        logger.info(f"Registered extension: {extension.name} v{extension.version}")

    def get(self, name: str) -> Optional[Extension]:
        """Get an extension by name.

        Args:
            name: Extension name

        Returns:
            Extension instance or None
        """
        return self.extensions.get(name)

    def activate_all(self) -> None:
        """Activate all registered extensions."""
        for extension in self.extensions.values():
            extension.activate()
        logger.info(f"Activated {len(self.extensions)} extensions")

    def list_extensions(self) -> List[Dict[str, Any]]:
        """List all registered extensions.

        Returns:
            List of extension information dictionaries
        """
        return [
            {
                "name": ext.name,
                "version": ext.version,
                "middleware_count": len(ext.middleware),
                "startup_hooks_count": len(ext.startup_hooks),
                "shutdown_hooks_count": len(ext.shutdown_hooks),
            }
            for ext in self.extensions.values()
        ]


# Global extension registry instance
_extension_registry: Optional[ExtensionRegistry] = None


def get_extension_registry() -> ExtensionRegistry:
    """Get the global extension registry instance.

    Returns:
        ExtensionRegistry instance
    """
    global _extension_registry
    if _extension_registry is None:
        _extension_registry = ExtensionRegistry()
    return _extension_registry



