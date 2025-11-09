"""
AiChemistForge - Unified MCP Server with integrated reasoning tools.

This package provides a unified MCP server built with FastMCP that includes:
- File system analysis tools (file_tree, codebase_ingest)
- Sequential thinking and reasoning capabilities
- Dependency analysis and problem decomposition

The server uses pure static tool registration with the @mcp.tool() decorator
for clean, efficient operation following MCP best practices.
"""

__version__ = "1.0.0"
__author__ = "Steve"
__email__ = "steve@simpleflowworks.com"

# Export the main FastMCP app for external use
from .main import mcp as fastmcp_app

__all__ = ["fastmcp_app"]
