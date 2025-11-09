"""
Reasoning tools for the unified MCP server.

This module contains tools for sequential thinking and reasoning capabilities.
"""

from .analyze_dependencies_tool import register_analyze_dependencies_tool
from .decompose_and_think_tool import register_decompose_and_think_tool

__all__ = [
    "register_analyze_dependencies_tool",
    "register_decompose_and_think_tool",
]
