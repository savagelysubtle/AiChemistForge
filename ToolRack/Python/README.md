# AiChemistForge - Python Unified MCP Server

A comprehensive Model Context Protocol (MCP) server built with Python 3.13+ and FastMCP, providing a collection of organized tools designed to assist AI development workflows. This server is part of the larger AiChemistForge project but can be run and developed as a standalone service.

## Features

- **FastMCP-Based**: Built on FastMCP 2.0+ for robust MCP protocol handling
- **Auto-Discovery**: Tools are automatically discovered and registered via registration functions
- **Type Safety**: Full type hints with Pydantic validation for all tool inputs
- **Robust Error Handling**: Comprehensive error handling following MCP transport best practices
- **Lifecycle Management**: Startup/shutdown hooks for resource management
- **Metrics & Tracing**: Built-in metrics collection and request tracing (configurable)
- **Middleware Support**: Rate limiting, timing, and extensible middleware chain
- **Caching**: LRU cache with TTL support for improved performance
- **Stdio Transport**: Primary transport mode optimized for local development and Cursor integration
- **HTTP Transport**: Optional HTTP/SSE transport for web access

## Current Tools

### Filesystem Tools

- **`file_tree`**: Generate comprehensive file tree structures with LLM optimization
  - Token counting and complexity analysis
  - Component extraction (functions, classes, methods)
  - Pattern filtering (include/exclude glob patterns)
  - Multiple output formats (tree, JSON, flat)
  - Smart chunking for large codebases
  - Language detection and metadata

- **`codebase_ingest`**: Process entire codebases for LLM context preparation
  - Intelligent file chunking strategies
  - Component extraction and complexity analysis
  - Language detection and statistics
  - Configurable file size limits and patterns
  - Structured or markdown output formats
  - LLM-optimized formatting with emojis and summaries

### Reasoning Tools

- **`decompose_and_think`**: Decompose complex problems with sequential thinking
  - Problem decomposition by domain (technical, analytical, creative, general)
  - Dependency analysis between sub-problems
  - Sequential thinking steps for each sub-problem
  - Critical path identification and bottleneck detection
  - Optional reflection and success criteria evaluation
  - Execution order recommendations

- **`analyze_dependencies`**: Analyze component dependencies and relationships
  - Dependency graph construction
  - Circular dependency detection
  - Critical path analysis
  - Bottleneck identification
  - Execution order recommendations
  - Relationship types: `depends_on`, `blocks`, `enables`, `integrates_with`

## Installation

### Prerequisites

- Python 3.13 or newer
- [UV Package Manager](https://github.com/astral-sh/uv)

### Setup Instructions

1. **Navigate to the Server Directory:**
   ```bash
   cd AiChemistForge/ToolRack/Python
   ```

2. **Install Dependencies using UV:**
   ```bash
   uv sync --all-groups
   ```
   This installs all dependencies including development tools (pytest, ruff, mypy).

3. **Set up Environment Variables (Optional):**
   Create a `.env` file in the project root with your configuration:
   ```bash
   # Server Configuration
   MCP_SERVER_NAME=aichemistforge-mcp-server
   MCP_LOG_LEVEL=INFO
   MCP_TRANSPORT_TYPE=stdio

   # File System Settings
   MAX_FILE_SIZE=10000000
   ALLOWED_PATHS=

   # Performance Tuning
   OPERATION_TIMEOUT=30.0
   CACHE_MAX_SIZE=1000
   CACHE_DEFAULT_TTL=300.0

   # Monitoring (optional)
   METRICS_ENABLED=true
   TRACING_ENABLED=true

   # Middleware (optional)
   RATE_LIMIT_ENABLED=false
   RATE_LIMIT_MAX_REQUESTS=100
   RATE_LIMIT_WINDOW_SECONDS=60.0
   ```

## Usage

### Running the Server

#### Windows (Batch Script)

```bash
# Standard mode
start_mcp_server.bat

# Debug mode (verbose logging)
start_mcp_server.bat --debug
```

#### Cross-Platform (Manual)

```bash
# Stdio transport (default, recommended for MCP clients)
uv run python -m unified_mcp_server.main --stdio

# Debug mode
uv run python -m unified_mcp_server.main --stdio --debug

# HTTP transport (for web access)
uv run python -m unified_mcp_server.main --http --host localhost --port 9876

# SSE transport (legacy)
uv run python -m unified_mcp_server.main --sse --host localhost --port 9876
```

### Connecting from an MCP Client (e.g., Cursor)

1. **Open Cursor Settings:**
   Navigate to `Features > Model Context Protocol`

2. **Add Server Configuration:**
   ```json
   {
     "mcpServers": {
       "aichemistforge-python": {
         "command": "D:\\path\\to\\AiChemistForge\\ToolRack\\Python\\start_mcp_server.bat",
         "cwd": "D:\\path\\to\\AiChemistForge\\ToolRack\\Python"
       }
     }
   }
   ```

   **Note:** Use absolute paths with double backslashes (`\\`) on Windows.

3. **Project-Level Configuration (Optional):**
   Create `.cursor/mcp.json` in your project root with the same configuration.

### Available Tools After Connection

Once connected, the following tools will be available:
- `file_tree` - Comprehensive file tree generation
- `codebase_ingest` - Codebase ingestion for LLM context
- `decompose_and_think` - Problem decomposition with sequential thinking
- `analyze_dependencies` - Component dependency analysis

## Configuration

The server supports extensive configuration via environment variables. Key settings:

### Server Settings
- `MCP_SERVER_NAME`: Server name (default: `aichemistforge-mcp-server`)
- `MCP_LOG_LEVEL`: Logging level - `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: `INFO`)
- `MCP_TRANSPORT_TYPE`: Transport type - `stdio`, `http`, `sse` (default: `stdio`)

### File System Settings
- `MAX_FILE_SIZE`: Maximum file size in bytes (default: `10000000` = 10MB)
- `ALLOWED_PATHS`: Comma-separated list of allowed paths (empty = all allowed)
- `ENABLE_PATH_TRAVERSAL_CHECK`: Enable path traversal protection (default: `true`)

### Performance Tuning
- `OPERATION_TIMEOUT`: Default timeout for operations in seconds (default: `30.0`)
- `RETRY_MAX_ATTEMPTS`: Maximum retry attempts (default: `3`)
- `MAX_CONCURRENT_OPERATIONS`: Maximum concurrent operations (default: `10`)
- `CACHE_MAX_SIZE`: Maximum cache entries (default: `1000`)
- `CACHE_DEFAULT_TTL`: Default cache TTL in seconds (default: `300.0`)

### Monitoring
- `METRICS_ENABLED`: Enable metrics collection (default: `true`)
- `TRACING_ENABLED`: Enable request tracing (default: `true`)
- `HEALTH_CHECK_ENABLED`: Enable health check endpoint (default: `true`)

### Middleware
- `RATE_LIMIT_ENABLED`: Enable rate limiting (default: `false`)
- `RATE_LIMIT_MAX_REQUESTS`: Maximum requests per window (default: `100`)
- `RATE_LIMIT_WINDOW_SECONDS`: Rate limit window in seconds (default: `60.0`)
- `RATE_LIMIT_PER_TOOL`: Apply rate limit per tool vs global (default: `false`)

## Development

### Project Structure

```
src/unified_mcp_server/
├── main.py                 # Server entry point with FastMCP initialization
├── server/                 # Core server infrastructure
│   ├── config.py          # Configuration management (Pydantic models)
│   ├── logging.py         # Contextual logging setup
│   ├── lifecycle.py        # Startup/shutdown lifecycle management
│   ├── metrics.py          # Metrics collection
│   ├── tracing.py          # Request tracing
│   ├── middleware.py       # Middleware chain (rate limiting, timing)
│   ├── resources.py        # Resource pool management
│   ├── context.py          # Context management
│   └── error_handling.py   # Error handling utilities
├── tools/                  # Tool implementations
│   ├── discovery.py        # Automatic tool discovery system
│   ├── filesystem/         # Filesystem tools
│   │   ├── file_tree_tool.py
│   │   └── codebase_ingest_tool.py
│   ├── reasoning/          # Reasoning and analysis tools
│   │   ├── decompose_and_think_tool.py
│   │   ├── analyze_dependencies_tool.py
│   │   ├── helpers.py      # Shared helper functions
│   │   └── validation.py   # Input validation utilities
│   └── code_execution/     # Code execution tools (if any)
└── utils/                  # Utility modules
    ├── caching.py          # LRU cache with TTL
    ├── composition.py      # Tool composition utilities
    ├── exceptions.py       # Custom exception classes
    ├── security.py         # Security utilities (path validation, sanitization)
    └── validators.py        # Input validation helpers
```

### Adding New Tools

Tools are automatically discovered via registration functions. To add a new tool:

1. **Create a Registration Function:**
   ```python
   from fastmcp import FastMCP
   from pydantic import BaseModel, Field
   from typing import Dict, Any
   import logging

   logger = logging.getLogger("mcp.tools.my_category")

   def register_my_tool(mcp: FastMCP) -> None:
       """Register the my_tool with the FastMCP instance."""

       @mcp.tool()
       async def my_tool(
           param1: str = Field(description="Description for parameter 1"),
           param2: int = Field(default=0, description="Optional parameter 2"),
       ) -> Dict[str, Any]:
           """Tool description for the MCP client."""
           logger.debug(f"Executing my_tool with param1={param1}")

           # Your tool logic here
           result = await some_async_operation(param1, param2)

           return {
               "success": True,
               "result": result,
               "tool": "my_tool",
           }
   ```

2. **Place the Tool File:**
   Save your tool file (e.g., `my_tool.py`) in an appropriate category directory:
   - `src/unified_mcp_server/tools/filesystem/` - Filesystem operations
   - `src/unified_mcp_server/tools/reasoning/` - Analysis and reasoning
   - `src/unified_mcp_server/tools/custom/` - Create new category as needed

3. **Automatic Discovery:**
   The discovery system (`tools/discovery.py`) automatically finds functions matching the pattern `register_*_tool` or `register_*_tools` and calls them during server startup. No manual registration needed!

4. **Export in `__init__.py` (Optional):**
   For better organization, you can export the registration function:
   ```python
   # tools/my_category/__init__.py
   from .my_tool import register_my_tool

   __all__ = ["register_my_tool"]
   ```

### Testing

Run tests using pytest:

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_specific_tool.py -v

# Run with coverage
uv run pytest tests/ --cov=unified_mcp_server --cov-report=html

# Test server connection
uv run python test_mcp_server.py
```

### Code Quality

The project uses Ruff for formatting and linting, and Mypy for type checking:

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check --fix .

# Type checking
uv run mypy src/
```

## Architecture

### Core Components

- **FastMCP Server** (`main.py`): FastMCP instance handles all MCP protocol communication
- **Tool Discovery** (`tools/discovery.py`): Automatically discovers and registers tools via registration functions
- **Server Config** (`server/config.py`): Pydantic-based configuration with environment variable support
- **Lifecycle Manager** (`server/lifecycle.py`): Manages startup/shutdown hooks for resource initialization
- **Metrics Collector** (`server/metrics.py`): Collects performance metrics (configurable)
- **Tracer** (`server/tracing.py`): Request tracing with correlation IDs (configurable)
- **Middleware Chain** (`server/middleware.py`): Extensible middleware for rate limiting, timing, etc.
- **Cache Manager** (`utils/caching.py`): LRU cache with TTL for performance optimization

### Design Principles

- **FastMCP Integration**: Leverages FastMCP decorators for tool registration (no custom BaseTool class)
- **Auto-Discovery**: Tools are automatically discovered via function naming conventions
- **Type Safety**: Full type hints with Pydantic validation for all inputs
- **Error Handling**: Comprehensive error handling following MCP transport best practices
- **Stdio Logging**: All logs go to stderr, JSON-RPC to stdout per MCP guidelines
- **Resource Management**: Proper lifecycle management with startup/shutdown hooks
- **Extensibility**: Easy to add new tools without modifying core server code
- **Configuration-Driven**: Behavior controlled via environment variables

### Transport Modes

- **Stdio** (Default): Standard input/output for MCP clients like Cursor
- **HTTP** (Streamable): Full bidirectional streaming over HTTP
- **SSE** (Legacy): Server-Sent Events transport (deprecated, use HTTP instead)

## Utilities

The server includes several utility modules:

- **`utils/caching.py`**: LRU cache with TTL support for caching tool results
- **`utils/security.py`**: Path validation, sanitization, and security checks
- **`utils/validators.py`**: Input validation helpers
- **`utils/composition.py`**: Tool composition and workflow utilities
- **`utils/exceptions.py`**: Custom exception classes for better error handling

## Troubleshooting

### Server Won't Start

1. **Check Python Version:**
   ```bash
   python --version  # Should be 3.13+
   ```

2. **Verify Dependencies:**
   ```bash
   uv sync --all-groups
   ```

3. **Check Logs:**
   Server logs appear on stderr. Check for import errors or configuration issues.

### Tools Not Discovered

1. **Verify Function Naming:**
   Registration functions must match pattern: `register_*_tool` or `register_*_tools`

2. **Check Module Imports:**
   Ensure the tool module is importable and doesn't have syntax errors

3. **Enable Debug Logging:**
   ```bash
   start_mcp_server.bat --debug
   ```
   Look for "Discovered registration function" messages

### Connection Issues

1. **Verify Paths:**
   Use absolute paths in MCP client configuration

2. **Check Permissions:**
   Ensure the server script has execute permissions

3. **Test Manually:**
   Run the server manually to verify it starts correctly:
   ```bash
   uv run python -m unified_mcp_server.main --stdio
   ```

## Contributing

When contributing to this Python MCP server:

1. **Follow Code Style**: Use Ruff formatter (line length: 88)
2. **Type Hints**: All functions must have complete type hints
3. **Error Handling**: Implement comprehensive error handling per MCP guidelines
4. **Logging**: Use structured logging to stderr (never stdout)
5. **Testing**: Add tests for new tools in `tests/`
6. **Documentation**: Update this README for new tools or features
7. **Tool Registration**: Use the `register_*_tool` function pattern for auto-discovery

## License

This project is licensed under the MIT License. Refer to the `LICENSE` file in the root of the AiChemistForge repository for details.

## Support

For issues, questions, or contributions:
- Check the parent AiChemistForge repository for issue tracking
- Review MCP documentation for protocol details
- See `CLAUDE.md` in the repository root for development guidelines
