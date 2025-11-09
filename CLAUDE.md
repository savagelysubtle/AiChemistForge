# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

AiChemistForge is a multi-language MCP (Model Context Protocol) server workspace. Each server in `ToolRack/` is self-contained and can run independently, but they follow consistent architectural patterns and MCP best practices.

**Server Implementations:**
- **Python** (`ToolRack/Python/`): Unified MCP server with task management, filesystem tools, database tools, and sequential reasoning
- **Rust** (`ToolRack/Rust/`): High-performance filesystem operations with security-conscious design
- **TypeScript** (`ToolRack/TypeScript/`): Brave Search API integration and Windows CLI tools
- **ObsidianGraph** (`ToolRack/ObsidianGraph/`): Obsidian knowledge graph server

**Development Environment:**
- Host: Windows 11 Pro
- Shell: PowerShell
- All MCP servers use stdio transport (logs to stderr, JSON-RPC to stdout per MCP specification)

## Build, Run, and Test Commands

### Python Server (ToolRack/Python)
```powershell
# Install dependencies
cd ToolRack/Python
uv sync --all-groups

# Run server (stdio transport)
.\start_mcp_server.bat
# Or manually:
uv run python -m unified_mcp_server.main --stdio

# Debug mode (verbose logging)
.\start_mcp_server.bat --debug

# HTTP transport (for web access)
.\start_mcp_server_http.bat
# Or:
uv run python -m unified_mcp_server.main --http --host localhost --port 9876

# Run tests
uv run python test_mcp_server.py

# Single test
uv run pytest tests/test_specific_tool.py -v
```

### Rust Server (ToolRack/Rust)
```powershell
# Build
cd ToolRack/Rust
cargo build --release

# Run server
.\start_mcp_server.bat

# Debug mode
.\start_mcp_server.bat --debug

# Run tests
cargo test

# Single test
cargo test test_name -- --nocapture
```

### TypeScript Server (ToolRack/TypeScript)
```powershell
# Install dependencies
cd ToolRack/TypeScript
npm install

# Build
npm run build

# Run server
npm start

# Development mode (auto-rebuild)
npm run dev

# Type checking
npm run lint
```

### ObsidianGraph Server (ToolRack/ObsidianGraph)
```powershell
cd ToolRack/ObsidianGraph
npm install
npm run build
npm test
```

## High-Level Architecture

### Python Server Architecture
**Core Pattern**: Task-based dynamic tool availability
- **Task State System** (`server/state.py`): Manages active tasks and determines which tools are available
- **Tool Organization**: Tools grouped by category (database/, filesystem/, reasoning/, composite/)
- **Tool Registration**: Each tool module exports a `register_*_tool(mcp)` function
- **FastMCP Integration**: Uses FastMCP for MCP protocol handling with decorator-based tool registration
- **Utilities Framework**: Comprehensive utils/ with exceptions, validation, security, caching, and composition

**Key Components:**
- `main.py`: Server entry point, registers all tools and handles transport selection
- `server/state.py`: `TaskState` class with workflow management
- `tools/tasks.py`: `TASK_TOOL_MAPPING` defines which tools are available for each task
- `utils/`: Security (path validation), caching (LRU with TTL), composition (tool workflows)

**Adding Python Tools:**
1. Create tool module in appropriate category folder (e.g., `tools/filesystem/my_tool.py`)
2. Implement `register_my_tool(mcp: FastMCP)` function
3. Import and call registration function in `main.py`
4. Tools auto-discovered if following BaseTool pattern

### Rust Server Architecture
**Core Pattern**: Enum-based tool registration with security layers
- **Security Model**: Forbidden directories list (`forbidden_dirs.txt`) - allows all except banned folders
- **Tool Enum** (`tools.rs`): `FileSystemTools` enum with `tool_box!` macro for registration
- **Write Access Control**: `require_write_access()` method flags tools that modify filesystem
- **Handler Pattern** (`handler.rs`): `MyServerHandler` implements MCP request handling

**Key Files:**
- `main.rs`: Entry point, creates server and handler
- `tools.rs`: Tool registration and write access checks
- `tools/`: Individual tool implementations (e.g., `read_file.rs`, `write_file.rs`)
- `fs_service.rs`: Core filesystem operations with security validation
- `task_state.rs`: Task management system

**Adding Rust Tools:**
1. Create tool module in `src/tools/` (e.g., `my_tool.rs`)
2. Define tool struct and implement logic
3. Add to `tools.rs`: `mod my_tool;` and include in `tool_box!` macro
4. Update `require_write_access()` if tool modifies filesystem

### TypeScript Server Architecture
**Core Pattern**: Zod schema validation with MCP SDK
- **Schema Definition**: Zod shapes define tool input schemas with type inference
- **Tool Metadata**: `Tool` objects define name, description, and inputSchema
- **Execution Functions**: Async functions handle tool logic and return `CallToolResult`
- **Server Registration**: `server.tool()` registers tools with name, schema, and handler

**Key Files:**
- `src/index.ts`: Entry point (imports and runs server)
- `src/server/server.ts`: MCP server setup, tool registration, stdio transport
- `src/tools/`: Tool implementations with Zod schemas
- `src/utils/logger.ts`: Stderr-only logging per MCP guidelines

**Adding TypeScript Tools:**
1. Create tool file in `src/tools/` (e.g., `myTool.ts`)
2. Define Zod shape, schema, Tool metadata, and execution function
3. Import and register in `src/server/server.ts` using `server.tool()`

## Development Standards

### Package Managers
- **Python**: UV (Astral package manager) - use `uv add`, `uv sync`, `uv run`
- **Rust**: Cargo - use `cargo add`, `cargo build`, `cargo test`
- **TypeScript**: npm - use `npm install`, `npm run build`

### Code Quality Tools
- **Python**: Ruff (formatter/linter), Mypy (type checker)
- **Rust**: rustfmt, clippy
- **TypeScript**: TypeScript compiler with strict mode

### Security Requirements
- **Never hard-code secrets**: Use environment variables (`.env` files provided as `.env.example`)
- **Input validation**: Python uses utils/validators.py, TypeScript uses Zod, Rust uses type system
- **Path security**: Python has utils/security.py for path traversal protection, Rust uses forbidden directories
- **Sanitization**: Python utils/security.py includes SQL injection, XSS, and command injection detection

### MCP Stdio Logging Guidelines
All servers follow MCP stdio transport best practices:
- **stdout**: Reserved exclusively for JSON-RPC messages
- **stderr**: All logging, debug output, and error messages
- Configure loggers to write to `sys.stderr` (Python), `eprintln!` (Rust), or custom stderr logger (TypeScript)
- Never use `print()` in Python or `console.log()` in TypeScript during runtime

### Type Safety
- **Python**: Type hints mandatory, avoid `Any` type, use Pydantic for validation
- **Rust**: Leverages Rust's type system, explicit error handling with `Result<T, E>`
- **TypeScript**: Strict mode enabled, Zod for runtime validation

### Documentation Style
- **Python**: Google-style docstrings for classes and large functions, NumPy-style for utilities
- **Rust**: Standard Rust doc comments (`///`)
- **TypeScript**: JSDoc comments where needed
- Keep concise, omit long examples unless essential

## MCP Client Configuration

### Cursor Settings Example
Add to Cursor's MCP settings (Features > Model Context Protocol):

```json
{
  "mcpServers": {
    "aichemistforge-python": {
      "command": "D:\\Coding\\AiChemistCodex\\AiChemistForge\\ToolRack\\Python\\start_mcp_server.bat",
      "cwd": "D:\\Coding\\AiChemistCodex\\AiChemistForge\\ToolRack\\Python"
    },
    "aichemistforge-rust": {
      "command": "D:\\Coding\\AiChemistCodex\\AiChemistForge\\ToolRack\\Rust\\start_mcp_server.bat",
      "cwd": "D:\\Coding\\AiChemistCodex\\AiChemistForge\\ToolRack\\Rust"
    },
    "aichemistforge-typescript": {
      "command": "node",
      "args": ["dist/index.js"],
      "cwd": "D:\\Coding\\AiChemistCodex\\AiChemistForge\\ToolRack\\TypeScript"
    }
  }
}
```

**Note**: Use absolute paths with double backslashes (`\\`) in JSON on Windows.

## Python Server Task Management System

The Python server uses a dynamic task-based tool availability system:

**Key Concepts:**
- **Task State** (`server/state.py`): Global state tracking current active task
- **Tool Mapping** (`tools/tasks.py`): `TASK_TOOL_MAPPING` defines available tools per task
- **Task Tools**: `start_task`, `complete_current_task`, `list_available_tasks`, `get_task_status`

**Workflow:**
1. Client calls `start_task(task_name="analyze_codebase")`
2. Server activates task and makes task-specific tools available
3. Client uses available tools (e.g., `file_tree`, `codebase_ingest`, `code_analysis`)
4. Client calls `complete_current_task()` to reset toolset

**Example Tasks:**
- `analyze_codebase`: Filesystem analysis tools
- `cursor_project_analysis`: Cursor database tools
- `sequential_thinking`: Reasoning and composition tools

## Security and Path Handling

### Python Server
- **Path Validation**: `utils/security.py` provides `is_path_safe()` and `validate_allowed_path()`
- **Input Sanitization**: Detects SQL injection, XSS, command injection patterns
- **Environment-Based Secrets**: All sensitive data via `.env` file

### Rust Server
- **Forbidden Directories**: Reads `forbidden_dirs.txt` (one path per line)
- **Allow-All-Except Model**: Permits access to all directories except those in forbidden list
- **Write Flag**: `--allow-write` flag required to enable write operations

### TypeScript Server
- **API Keys**: Brave API key required in `.env` as `BRAVE_API_KEY`
- **Rate Limiting**: Basic client-side rate limiting for API calls

## Common Debugging Tasks

### Check Python Server Tool Discovery
```powershell
cd ToolRack/Python
uv run python -c "from unified_mcp_server.tools.registry import ToolRegistry; print([t.name for t in ToolRegistry.discover_tools()])"
```

### View Rust Server Tools
```powershell
cd ToolRack/Rust
cargo run -- --help
# Or check tools.rs FileSystemTools enum
```

### Test TypeScript Tool Schema
```powershell
cd ToolRack/TypeScript
npm run build
node -e "import('./dist/tools/braveSearchTools.js').then(m => console.log(m.WEB_SEARCH_TOOL))"
```

## Additional Resources

- **Architecture Plans**: See `Plans/Python/` for detailed refactoring documentation
- **Progress Tracking**: `.cursor/AiChemistForge.md` contains development status
- **MCP Documentation**: Refer to `Compendium/` for MCP guides and examples
- **Project Standards**: `.cursor/rules/projectconfig.mdc` defines coding standards
