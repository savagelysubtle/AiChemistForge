"""Automatic tool discovery system for MCP server.

This module automatically discovers and registers tools from the tools directory,
allowing new tools to be added without modifying main.py.
"""

import importlib
import inspect
import logging
import pkgutil
from pathlib import Path
from typing import Callable, List

from fastmcp import FastMCP

logger = logging.getLogger("mcp.tools.discovery")


def discover_tool_registration_functions(
    package_path: str = "unified_mcp_server.tools",
) -> List[Callable[[FastMCP], None]]:
    """Discover all tool registration functions in the tools package.

    Scans the tools directory and subdirectories for modules containing
    functions that match the pattern `register_*_tool` or `register_*_tools`.

    Args:
        package_path: Python package path to scan (default: unified_mcp_server.tools)

    Returns:
        List of registration functions that accept FastMCP instance
    """
    registration_functions: List[Callable[[FastMCP], None]] = []

    try:
        # Import the tools package
        tools_package = importlib.import_module(package_path)

        # Walk through all modules in the package
        for importer, modname, ispkg in pkgutil.walk_packages(
            tools_package.__path__, tools_package.__name__ + "."
        ):
            # Skip __init__ and __pycache__
            if modname.endswith("__init__") or "__pycache__" in modname:
                continue

            try:
                # Import the module
                module = importlib.import_module(modname)

                # Look for registration functions
                for name, obj in inspect.getmembers(module):
                    # Check if it's a function and matches registration pattern
                    if inspect.isfunction(obj) and (
                        name.startswith("register_") and name.endswith(("_tool", "_tools"))
                    ):
                        # Verify it has the correct signature (accepts FastMCP)
                        sig = inspect.signature(obj)
                        params = list(sig.parameters.values())
                        if len(params) == 1 and params[0].annotation in (
                            FastMCP,
                            inspect.Parameter.empty,
                        ):
                            registration_functions.append(obj)
                            logger.debug(
                                f"Discovered registration function: {modname}.{name}"
                            )

            except Exception as e:
                logger.warning(f"Failed to import module {modname}: {e}")
                continue

    except Exception as e:
        logger.error(f"Error discovering tools: {e}", exc_info=True)

    return registration_functions


def register_all_tools(mcp: FastMCP, package_path: str = "unified_mcp_server.tools") -> int:
    """Automatically discover and register all tools.

    Scans the tools directory for registration functions and calls them
    to register tools with the FastMCP instance.

    Args:
        mcp: FastMCP server instance to register tools with
        package_path: Python package path to scan (default: unified_mcp_server.tools)

    Returns:
        Number of tools successfully registered
    """
    logger.info("Starting automatic tool discovery...")

    registration_functions = discover_tool_registration_functions(package_path)

    if not registration_functions:
        logger.warning("No tool registration functions found")
        return 0

    registered_count = 0
    for reg_func in registration_functions:
        try:
            reg_func(mcp)
            registered_count += 1
            logger.debug(f"Registered tools from: {reg_func.__module__}.{reg_func.__name__}")
        except Exception as e:
            logger.error(
                f"Failed to register tools from {reg_func.__module__}.{reg_func.__name__}: {e}",
                exc_info=True,
            )

    logger.info(f"Successfully registered {registered_count} tool module(s)")
    return registered_count



