"""Integration test for retry system with actual MCP tools."""

import asyncio
import tempfile
from pathlib import Path

import pytest

from unified_mcp_server.tools.filesystem.file_tree_tool import register_file_tree_tool
from unified_mcp_server.tools.filesystem.codebase_ingest_tool import (
    register_codebase_ingest_tool,
)

# Mock FastMCP for testing
class MockFastMCP:
    """Mock FastMCP for testing tool registration."""

    def __init__(self):
        self.tools = {}

    def tool(self):
        """Decorator to register tools."""

        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator


@pytest.mark.asyncio
async def test_file_tree_with_retry():
    """Test file_tree tool with retry decorator applied."""
    mcp = MockFastMCP()
    register_file_tree_tool(mcp)

    # Verify tool was registered
    assert "file_tree" in mcp.tools

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create some test files
        (tmppath / "test1.py").write_text("print('hello')")
        (tmppath / "test2.js").write_text("console.log('world')")
        (tmppath / "subdir").mkdir()
        (tmppath / "subdir" / "test3.txt").write_text("test content")

        # Call the tool
        result = await mcp.tools["file_tree"](
            path=str(tmppath),
            max_depth=3,
            show_sizes=True,
            show_tokens=True,
        )

        # Verify result
        assert result["success"] is True
        assert "result" in result
        assert "metadata" in result
        assert result["metadata"]["format"] == "tree"


@pytest.mark.asyncio
async def test_codebase_ingest_with_retry():
    """Test codebase_ingest tool with retry decorator applied."""
    mcp = MockFastMCP()
    register_codebase_ingest_tool(mcp)

    # Verify tool was registered
    assert "codebase_ingest" in mcp.tools

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create some test files
        (tmppath / "main.py").write_text(
            '''"""Main module."""\n\ndef main():\n    print("Hello, world!")\n'''
        )
        (tmppath / "utils.py").write_text(
            '''"""Utilities."""\n\ndef helper():\n    return "help"\n'''
        )

        # Call the tool
        result = await mcp.tools["codebase_ingest"](
            path=str(tmppath),
            output_format="structured",
        )

        # Verify result
        assert result["success"] is True
        assert "result" in result
        assert "metadata" in result
        assert result["metadata"]["files_processed"] >= 2


@pytest.mark.asyncio
async def test_file_tree_nonexistent_path():
    """Test file_tree with non-existent path (should fail without retry)."""
    mcp = MockFastMCP()
    register_file_tree_tool(mcp)

    # Call with non-existent path
    result = await mcp.tools["file_tree"](
        path="/nonexistent/path/that/does/not/exist",
        max_depth=3,
    )

    # Should return error without retry (path validation error)
    assert result["success"] is False
    assert "error" in result
    assert "does not exist" in result["error"].lower()


@pytest.mark.asyncio
async def test_codebase_ingest_empty_directory():
    """Test codebase_ingest with empty directory."""
    mcp = MockFastMCP()
    register_codebase_ingest_tool(mcp)

    # Create empty temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        result = await mcp.tools["codebase_ingest"](
            path=str(tmpdir),
            output_format="structured",
        )

        # Should succeed but with no files processed
        assert result["success"] is True
        assert "result" in result or "metadata" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

