"""Main entry point for the AiChemistForge MCP server - Unified Static Registration.

Enhanced with lifecycle management, metrics, tracing, middleware, and context management.
"""

import argparse
import asyncio
import logging
import signal
import sys

from fastmcp import FastMCP

# Import server components
from unified_mcp_server.server.config import load_config
from unified_mcp_server.server.context import get_context_manager
from unified_mcp_server.server.lifecycle import get_lifecycle_manager
from unified_mcp_server.server.logging import (
    setup_contextual_logging,
)
from unified_mcp_server.server.metrics import get_metrics_collector
from unified_mcp_server.server.middleware import (
    RateLimitConfig,
    RateLimitingMiddleware,
    create_default_middleware_chain,
    get_middleware_chain,
)
from unified_mcp_server.server.resources import get_resource_manager
from unified_mcp_server.server.tracing import get_tracer
from unified_mcp_server.tools.discovery import register_all_tools
from unified_mcp_server.utils.caching import cache_manager

# Load configuration
config = load_config()

# Create single FastMCP server instance
mcp = FastMCP("AiChemistForge")

logger = logging.getLogger("mcp.server")

# =============================================================================
#  SERVER INITIALIZATION
# =============================================================================

# Initialize server components
lifecycle_manager = get_lifecycle_manager()
resource_manager = get_resource_manager()
context_manager = get_context_manager()
metrics_collector = get_metrics_collector()
tracer = get_tracer()
middleware_chain = get_middleware_chain()

# Configure components based on config
if not config.metrics_enabled:
    metrics_collector.disable()

if not config.tracing_enabled:
    tracer.enabled = False

# Setup middleware chain
if config.rate_limit_enabled:
    rate_limit_config = RateLimitConfig(
        max_requests=config.rate_limit_max_requests,
        window_seconds=config.rate_limit_window_seconds,
        per_tool=config.rate_limit_per_tool,
    )
    middleware_chain.add(RateLimitingMiddleware(rate_limit_config))

# Add default middleware (timing, metrics)
default_chain = create_default_middleware_chain()
for middleware in default_chain.middlewares:
    middleware_chain.add(middleware)


# Register startup hooks
async def startup_cache() -> None:
    """Start cache manager on startup."""
    await cache_manager.start()


async def startup_resources() -> None:
    """Initialize resource pools on startup."""
    await resource_manager.initialize_all()


async def startup_metrics() -> None:
    """Initialize metrics collection on startup."""
    if config.metrics_enabled:
        metrics_collector.enable()


lifecycle_manager.register_startup_hook(
    startup_cache, "cache_manager", priority=10, async_callback=True
)
lifecycle_manager.register_startup_hook(
    startup_resources, "resource_pools", priority=20, async_callback=True
)
lifecycle_manager.register_startup_hook(
    startup_metrics, "metrics", priority=30, async_callback=True
)


# Register shutdown hooks
async def shutdown_cache() -> None:
    """Stop cache manager on shutdown."""
    await cache_manager.stop()


async def shutdown_resources() -> None:
    """Close resource pools on shutdown."""
    await resource_manager.close_all()


lifecycle_manager.register_shutdown_hook(
    shutdown_cache, "cache_manager", priority=10, async_callback=True
)
lifecycle_manager.register_shutdown_hook(
    shutdown_resources, "resource_pools", priority=20, async_callback=True
)

# =============================================================================
#  TOOL REGISTRATION
# =============================================================================

# Automatically discover and register all tools from the tools directory
# New tools are automatically loaded when added to any subdirectory in tools/
tool_count = register_all_tools(mcp)

logger.info(f"Tool discovery complete - registered {tool_count} tool module(s)")


def setup_signal_handlers() -> None:
    """Set up signal handlers for graceful shutdown following MCP best practices."""

    async def shutdown_async() -> None:
        """Async shutdown handler."""
        await lifecycle_manager.shutdown()

    def signal_handler(signum: int, frame) -> None:
        """Handle shutdown signals gracefully with proper resource cleanup."""
        # Log shutdown for debugging (will go to stderr)
        logging.getLogger("mcp.server").info(
            f"Received signal {signum}, shutting down gracefully"
        )
        try:
            # Run async shutdown
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Schedule shutdown
                    asyncio.create_task(shutdown_async())
                else:
                    loop.run_until_complete(shutdown_async())
            except RuntimeError:
                # No event loop, create one
                asyncio.run(shutdown_async())
            sys.exit(0)
        except Exception as e:
            logging.getLogger("mcp.server").error(f"Error during shutdown: {e}")
            sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def configure_stdio_logging(debug: bool = False) -> None:
    """Configure logging for stdio transport following MCP best practices.

    Per 1000-mcp-stdio-logging.mdc: logs should be easily viewable in the console
    while not interfering with stdio JSON-RPC communication.

    Enhanced with contextual logging for correlation IDs and structured fields.
    """
    # Use contextual logging if enabled in config
    if config.tracing_enabled:
        setup_contextual_logging("mcp", "DEBUG" if debug else config.log_level)
    else:
        # Fallback to simple logging
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        log_level = logging.DEBUG if debug else logging.INFO
        root_logger.setLevel(log_level)

        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(log_level)

        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S"
        )
        stderr_handler.setFormatter(formatter)
        root_logger.addHandler(stderr_handler)

    # Configure FastMCP logging to be visible but not overwhelming
    fastmcp_logger = logging.getLogger("fastmcp")
    fastmcp_logger.setLevel(logging.WARNING if not debug else logging.DEBUG)

    # Create server logger for our specific use
    server_logger = logging.getLogger("mcp.server")
    server_logger.setLevel(logging.DEBUG if debug else logging.INFO)


def setup_error_handling() -> None:
    """Setup comprehensive error handling per MCP transport best practices."""

    def handle_exception(exc_type, exc_value, exc_traceback):
        """Global exception handler for unhandled exceptions."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Handle keyboard interrupt gracefully
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Log unhandled exceptions
        logger = logging.getLogger("mcp.server")
        logger.critical(
            "Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = handle_exception


def main() -> int:
    """Main entry point for the MCP server following MCP best practices."""
    parser = argparse.ArgumentParser(description="AiChemistForge MCP Server")
    parser.add_argument(
        "--port", type=int, default=9876, help="Port to run the server on"
    )
    parser.add_argument(
        "--host", type=str, default="localhost", help="Host to bind the server to"
    )
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Use stdio transport (default for MCP clients)",
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="Use HTTP transport (streamable HTTP protocol)",
    )
    parser.add_argument(
        "--sse",
        action="store_true",
        help="Use SSE transport (legacy, use --http instead)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Setup error handling first
    setup_error_handling()

    # Configure logging based on transport type
    if not args.stdio:
        # For HTTP/SSE mode, we can use more verbose logging
        logging.basicConfig(
            level=logging.DEBUG if args.debug else logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            stream=sys.stderr,
        )
    else:
        # For stdio mode, configure per MCP guidelines
        configure_stdio_logging(args.debug)

    # Setup signal handlers
    setup_signal_handlers()

    # Get logger for this module
    logger = logging.getLogger("mcp.server")

    # Initialize server lifecycle
    async def initialize_server() -> None:
        """Initialize server components."""
        await lifecycle_manager.startup()

    # Run initialization
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Schedule initialization
            asyncio.create_task(initialize_server())
        else:
            loop.run_until_complete(initialize_server())
    except RuntimeError:
        # No event loop, create one
        asyncio.run(initialize_server())

    logger.info("Server initialization complete")

    try:
        # Determine transport type
        if args.stdio:
            # Use stdio transport for MCP clients (like Cursor) - preferred per MCP guidelines
            logger.info("Starting AiChemistForge MCP server with stdio transport")
            logger.info("Stdio transport selected - logs will appear on stderr")
            logger.debug(
                "Debug logging enabled" if args.debug else "Standard logging level"
            )
            mcp.run()  # FastMCP uses stdio by default
        elif args.http:
            # Use HTTP transport (streamable HTTP protocol) for web access
            logger.info(
                f"Starting AiChemistForge MCP server with HTTP transport (streamable) on {args.host}:{args.port}"
            )
            logger.info("This transport supports full bidirectional streaming")
            mcp.run(transport="streamable-http", host=args.host, port=args.port)
        elif args.sse:
            # Use SSE transport (legacy) - kept for backward compatibility
            logger.warning(
                "SSE transport is legacy - consider using --http for streamable HTTP instead"
            )
            logger.info(
                f"Starting AiChemistForge MCP server with SSE transport on {args.host}:{args.port}"
            )
            mcp.run(transport="sse", host=args.host, port=args.port)
        else:
            # Default behavior - stdio unless host/port are specified
            if args.host != "localhost" or args.port != 9876:
                # If host/port are specified, default to HTTP transport
                logger.info(
                    f"Starting AiChemistForge MCP server with HTTP transport (streamable) on {args.host}:{args.port}"
                )
                logger.info("Use --stdio to force stdio transport instead")
                mcp.run(transport="streamable-http", host=args.host, port=args.port)
            else:
                # Otherwise default to stdio for MCP compatibility
                logger.info("Starting AiChemistForge MCP server with stdio transport")
                logger.info("Use --http or specify --host/--port for network access")
                mcp.run()  # FastMCP uses stdio by default

    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
        return 0
    except Exception as e:
        logger.error(f"Server startup failed: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
