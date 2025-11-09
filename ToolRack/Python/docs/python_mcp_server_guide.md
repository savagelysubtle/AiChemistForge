# Python MCP Server Documentation & Troubleshooting Guide

## Overview

Model Context Protocol (MCP) servers enable AI assistants to securely connect to data sources and tools. This guide covers Python MCP server implementations, setup, and troubleshooting.

## Best Python MCP Server Libraries

### 1. Official Python Template (Recommended)
- **Library ID**: `/modelcontextprotocol/create-python-server`
- **Trust Score**: 7.8
- **Description**: Official template for creating MCP server projects with zero build configuration
- **Best For**: New projects, following official patterns

```bash
# Using uvx (recommended)
uvx create-python-server my-mcp-server
cd my-mcp-server
```

### 2. FastMCP (High Performance)
- **Library ID**: `/pietrozullo/mcp-use`
- **Trust Score**: 6.6
- **Code Snippets**: 358
- **Description**: High-performance Python MCP server framework
- **Best For**: Complex servers with many tools

```python
from fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
async def my_tool(param: str) -> str:
    return f"Processed: {param}"

if __name__ == "__main__":
    mcp.run()
```

### 3. Specialized MCP Servers (Copy & Adapt)

#### Database Access
- **Library ID**: `/executeautomation/mcp-database-server`
- **Trust Score**: 9.7
- **Supports**: SQLite, SQL Server, PostgreSQL, MySQL

#### File System Operations
- **Library ID**: `/cyanheads/filesystem-mcp-server`
- **Trust Score**: 9.1
- **Features**: Secure file system access with path validation

#### Code Execution
- **Library ID**: `/bazinga012/mcp_code_executor`
- **Trust Score**: 6.9
- **Features**: Execute Python code in controlled environment

## Common Connection Issues & Solutions

### 1. Stdio Transport Issues (Most Common)

**Problem**: Server not responding via stdio transport
```bash
# Symptoms
- Server starts but no response from client
- JSON-RPC communication failures
- Client timeouts
```

**Solution**: Ensure proper stdio configuration
```python
# main.py - Correct stdio setup
import sys
import json
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server

async def main():
    server = Server("my-server")

    # Register tools here
    @server.list_tools()
    async def list_tools():
        return [{"name": "example", "description": "Example tool"}]

    # Critical: Use stdio_server for MCP clients
    async with stdio_server() as streams:
        await server.run(streams[0], streams[1])

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Logging Interference

**Problem**: Logs interfering with JSON-RPC communication
```python
# Wrong - logs to stdout
import logging
logging.basicConfig(stream=sys.stdout)  # DON'T DO THIS

# Correct - logs to stderr
import logging
logging.basicConfig(
    stream=sys.stderr,  # Use stderr for MCP compatibility
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
```

### 3. FastMCP Connection Issues

**Problem**: FastMCP server not connecting
```python
# Check your main.py setup
from fastmcp import FastMCP

mcp = FastMCP("AiChemistForge_Dynamic")

# Ensure tools are registered before run()
@mcp.tool()
async def test_tool() -> dict:
    return {"status": "working"}

# Common issues:
if __name__ == "__main__":
    # Wrong: Missing connection details
    # mcp.run()

    # Correct: Explicit transport
    mcp.run()  # Uses stdio by default
    # OR for HTTP:
    # mcp.run(transport="http", port=8000)
```

### 4. Client Configuration Issues

**Cursor IDE Configuration** (`~/.cursor/mcp_servers.json`):
```json
{
  "mcpServers": {
    "your-server": {
      "command": "python",
      "args": [
        "-m", "your_package.main"
      ],
      "cwd": "/path/to/your/project"
    }
  }
}
```

**Claude Desktop Configuration** (`~/AppData/Roaming/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "your-server": {
      "command": "python",
      "args": ["/path/to/your/server/main.py"],
      "env": {
        "PYTHONPATH": "/path/to/your/project"
      }
    }
  }
}
```

## Debugging Steps

### 1. Test Server Independently
```bash
# Test your server directly
python main.py --stdio

# Should see logs on stderr, not hang
# Test with simple JSON-RPC message:
echo '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' | python main.py --stdio
```

### 2. Check Dependencies
```bash
# For official template
pip install mcp

# For FastMCP
pip install fastmcp

# For database servers
pip install sqlalchemy databases

# Common missing dependencies
pip install pydantic typing-extensions
```

### 3. Validate JSON-RPC Communication
```python
# Add debug logging to see messages
import logging
import sys

logging.basicConfig(
    stream=sys.stderr,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)

# In your server setup
async def handle_request(request):
    logger.debug(f"Received request: {request}")
    # ... process request
    logger.debug(f"Sending response: {response}")
    return response
```

### 4. Path and Import Issues
```python
# common_issues.py
import sys
from pathlib import Path

# Add your project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Now import your modules
try:
    from your_package import your_module
    print("✓ Imports working")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
```

## Working Example: Minimal Python MCP Server

```python
# minimal_server.py
import asyncio
import logging
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Setup logging to stderr (MCP requirement)
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("minimal-mcp-server")

# Create server
server = Server("minimal-server")

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="echo",
            description="Echo back the input",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Message to echo"}
                },
                "required": ["message"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name == "echo":
        message = arguments.get("message", "")
        logger.info(f"Echo tool called with: {message}")
        return [TextContent(type="text", text=f"Echo: {message}")]
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Run the server."""
    logger.info("Starting minimal MCP server...")
    try:
        async with stdio_server() as streams:
            await server.run(streams[0], streams[1])
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())
```

Test this server:
```bash
python minimal_server.py
```

## Troubleshooting Checklist

- [ ] Logs going to stderr, not stdout
- [ ] Using correct transport (stdio for MCP clients)
- [ ] All dependencies installed
- [ ] Python path includes your project
- [ ] Server responds to basic JSON-RPC messages
- [ ] Client configuration points to correct script
- [ ] No syntax errors in server code
- [ ] Tools properly registered before server.run()

## Getting Help

1. **Check server logs**: Look at stderr output for error messages
2. **Test incrementally**: Start with minimal server, add features gradually
3. **Validate JSON-RPC**: Use tools like `jq` to test message format
4. **Client logs**: Check your MCP client's logs for connection errors

## Resources

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Official Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [FastMCP Documentation](https://github.com/pierrot-zl/fastmcp)
- [MCP Server Examples](https://github.com/modelcontextprotocol/servers)