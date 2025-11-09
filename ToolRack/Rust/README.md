# AiChemistForge - Rust Filesystem MCP Server

A high-performance, asynchronous Model Context Protocol (MCP) server built with
Rust and Tokio, providing comprehensive filesystem operations for AI development
workflows. This server is part of the larger AiChemistForge project but can be
compiled, run, and utilized as a standalone component.

## Features

- **⚡ High Performance**: Built with Rust and Tokio for asynchronous,
  non-blocking I/O
- **🔒 Security Conscious**: Two-tier blocklist system - blocks specific
  directories while allowing others
- **📦 Composite Tools**: Dynamic operation mode system groups related
  operations for better organization
- **✍️ Read-Write Mode**: Full read-write access by default (no read-only mode)
- **🔄 Operation Modes**: Context-aware tool availability via operation mode
  management
- **📊 Workflow Tracking**: Built-in workflow history and step tracking for
  operation modes
- **🔍 Advanced Search**: Powerful file and directory searching with glob
  patterns and content search
- **📁 Comprehensive Operations**: Wide range of file/directory manipulation,
  reading, writing, and metadata retrieval
- **📦 Standalone Binary**: Compiles to a single native executable with no
  external runtime dependencies
- **⚖️ Lightweight**: Minimal resource footprint, suitable for various
  deployment scenarios

## Architecture

### Dynamic Operation Mode System

The server uses a **composite tool architecture** where individual operations
are grouped into operation modes:

- **`single_file_operations`**: Operations on individual files (read, write,
  edit, info, head, tail, lines, media)
- **`multiple_file_operations`**: Batch operations on multiple files (read,
  copy, move, delete)
- **`directory_operations`**: Directory-level operations (create, list, tree,
  size, find empty)
- **`search_and_analysis`**: Search and analysis tools (search files, search
  content, find duplicates)
- **`file_management`**: File management operations (zip, unzip, move, copy,
  delete)

### Operation Mode Management

The server includes operation mode management tools that enable context-aware
tool availability:

- **`start_operation_mode`**: Activate a specific operation mode (enables
  related tools)
- **`complete_current_mode`**: Complete the current mode and return to default
  state
- **`list_available_modes`**: List all available operation modes
- **`get_current_mode_status`**: Get status and workflow history of current mode

### Security Model

**Two-Tier Blocklist System:**

1. **Default Blocklist** (Automatic): System-critical directories from
   `forbidden_dirs.txt`

   - `C:\Windows`, `C:\Program Files`, `C:\ProgramData`, etc.
   - Always applied when using `start_mcp_server.bat`

2. **Custom Blocklist** (Optional): Additional directories via command-line or
   MCP config
   - Comma-separated list: `--blocked-directories "D:\Sensitive,C:\Private"`
   - Merged with default blocklist

**Access Model**: Allow all directories **except** blocked ones (with optional
allowlist for restricted mode)

## Available Tools

### Composite Operation Tools

#### Single File Operations (`single_file_operations`)

- **`read_file`**: Read entire file content
- **`write_file`**: Write content to file (create or overwrite)
- **`edit_file`**: Perform line-based edits with diff preview
- **`get_file_info`**: Get detailed file/directory metadata
- **`head_file`**: Read first N lines of a file
- **`tail_file`**: Read last N lines of a file
- **`read_file_lines`**: Read specific line range from file
- **`read_media_file`**: Read media files (images, audio, video) as base64

#### Multiple File Operations (`multiple_file_operations`)

- **`read_multiple_files`**: Read content from multiple files in batch
- **`read_multiple_media_files`**: Read multiple media files as base64
- **`copy_file`**: Copy files or directories
- **`move_file`**: Move or rename files/directories
- **`delete_file`**: Delete files or directories

#### Directory Operations (`directory_operations`)

- **`create_directory`**: Create directories (with parent creation)
- **`list_directory`**: List directory contents
- **`list_directory_with_sizes`**: List directory with file sizes
- **`directory_tree`**: Generate recursive tree view
- **`calculate_directory_size`**: Calculate total size of directory
- **`find_empty_directories`**: Find empty directories recursively

#### Search and Analysis (`search_and_analysis`)

- **`search_files`**: Search for files/directories matching glob patterns
- **`search_files_content`**: Search file contents using regex patterns
- **`find_duplicate_files`**: Find duplicate files by content hash

#### File Management (`file_management`)

- **`zip_files`**: Compress multiple files into ZIP archive
- **`zip_directory`**: Compress entire directory into ZIP archive
- **`unzip_file`**: Decompress ZIP archive

### Operation Mode Management Tools

- **`start_operation_mode`**: Start a new operation mode
- **`complete_current_mode`**: Complete current operation mode
- **`list_available_modes`**: List all available operation modes
- **`get_current_mode_status`**: Get current mode status and workflow history

### Utility Tools

- **`list_allowed_directories`**: List directories the server is permitted to
  access

## Installation & Building

### Prerequisites

- **Rust Toolchain**: Rust 1.70+ installed via [rustup](https://rustup.rs/)
- **Windows**: Batch scripts provided for Windows (Linux/Mac users need
  equivalent shell scripts)

### Quick Start (Windows)

1. **Navigate to the Server Directory:**

   ```batch
   cd AiChemistForge/ToolRack/Rust
   ```

2. **Build the Server:**

   ```batch
   build_mcp_server.bat
   ```

   This creates a release build at
   `target/release/aichemistforge-mcp-server.exe`

3. **Run the Server:**
   ```batch
   start_mcp_server.bat
   ```
   Or with debug logging:
   ```batch
   start_mcp_server.bat --debug
   ```

### Building the Server

**Important:** Build and run are separated for faster startup:

- **`build_mcp_server.bat`** - Run when you change code (compiles to release
  binary)
- **`start_mcp_server.bat`** - Run to start server (uses pre-built binary, no
  rebuild)

**Manual Build Commands:**

```bash
# Release build (optimized, recommended)
cargo build --release

# Debug build (faster compile, slower runtime)
cargo build
```

The compiled binary will be located in:

- Release: `target/release/aichemistforge-mcp-server.exe`
- Debug: `target/debug/aichemistforge-mcp-server.exe`

## Usage

### Running the Server Directly

```bash
# Using cargo run (from ToolRack/Rust/ directory)
cargo run --release -- --blocked-directories "C:\Windows,C:\Program Files" [ALLOWED_PATH_1] [ALLOWED_PATH_2] ...

# Using pre-built binary
target/release/aichemistforge-mcp-server.exe --blocked-directories "C:\Windows,C:\Program Files"
```

**Command-Line Arguments:**

- `--blocked-directories DIR1,DIR2,DIR3`: Comma-separated list of blocked
  directories
- `[ALLOWED_PATH_1] [ALLOWED_PATH_2] ...`: Optional space-separated allowed
  directories (empty = unrestricted except blocked)

**Examples:**

```bash
# Unrestricted mode with blocklist (recommended)
cargo run --release -- --blocked-directories "C:\Windows,C:\Program Files"

# Restricted mode with allowlist
cargo run --release -- D:\Projects\Project1 D:\Projects\Project2

# Combined: allowlist + additional blocklist
cargo run --release -- --blocked-directories "D:\Sensitive" D:\Projects\Project1
```

### Connecting from an MCP Client (e.g., Cursor)

1. **Build the server first:**

   ```batch
   cd ToolRack/Rust
   build_mcp_server.bat
   ```

2. **Configure MCP Client:** Add to Cursor's MCP settings (`.cursor/mcp.json` or
   global settings):

   ```json
   {
     "mcpServers": {
       "aichemistforge-rust": {
         "command": "D:\\path\\to\\AiChemistForge\\ToolRack\\Rust\\start_mcp_server.bat",
         "args": [],
         "type": "stdio",
         "env": {
           "RUST_LOG": "info"
         }
       }
     }
   }
   ```

3. **Add Custom Blocked Directories (Optional):**

   ```json
   {
     "mcpServers": {
       "aichemistforge-rust": {
         "command": "D:\\path\\to\\AiChemistForge\\ToolRack\\Rust\\start_mcp_server.bat",
         "args": [
           "--blocked-directories",
           "D:\\SensitiveProject,C:\\PrivateData"
         ],
         "type": "stdio",
         "env": {
           "RUST_LOG": "debug"
         }
       }
     }
   }
   ```

4. **Restart Cursor** to load the MCP server configuration

5. **Verify Connection:**
   - Open Cursor's command palette (Ctrl+Shift+P)
   - Search for "MCP" commands
   - You should see the Rust server listed with available tools

## Configuration

### Default Blocked Directories

The `forbidden_dirs.txt` file contains default blocked directories that are
automatically applied:

```txt
C:\Windows
C:\Windows\System32
C:\Program Files
C:\Program Files (x86)
C:\ProgramData
C:\System Volume Information
C:\$Recycle.Bin
C:\Recovery
```

**To customize:** Edit `forbidden_dirs.txt` and add/remove directories (one per
line, `#` for comments)

### Environment Variables

- **`RUST_LOG`**: Logging level (`error`, `warn`, `info`, `debug`, `trace`)
  - Default: `warn` (set to `debug` for verbose logging)

### Security Configuration

**Default Behavior (Recommended):**

- All directories allowed **except** those in blocklist
- System directories automatically blocked
- Custom directories can be added to blocklist

**Restricted Mode:**

- Specify allowed directories as command-line arguments
- Only those directories accessible (plus blocklist still applies)

## Development

### Project Structure

```plaintext
src/
├── main.rs                    # Entry point, server initialization
├── server.rs                  # MCP server implementation
├── handler.rs                 # Request handler (tool routing)
├── cli.rs                     # Command-line argument parsing
├── error.rs                   # Error types and handling
├── mcp_types.rs               # MCP protocol type definitions
├── task_state.rs              # Operation mode and workflow state management
├── fs_service.rs              # Filesystem service (path validation, operations)
│   ├── file_info.rs          # File metadata structures
│   └── utils.rs              # Path utilities (normalization, expansion)
└── tools/                     # Tool implementations
    ├── mod.rs                # Tool module exports and enum definitions
    ├── single_file_operations.rs
    ├── multiple_file_operations.rs
    ├── directory_operations.rs
    ├── search_and_analysis.rs
    ├── file_management.rs
    ├── operation_mode_management.rs
    └── [individual tool modules]
```

### Adding New Tools

1. **Create Tool Module:** Create a new file in `src/tools/` (e.g.,
   `my_tool.rs`):

   ```rust
   use serde::{Deserialize, Serialize};
   use serde_json::json;
   use crate::mcp_types::{Tool, CallToolResult, Content, TextContent, CallToolError};
   use crate::fs_service::FileSystemService;

   #[derive(Debug, Clone, Serialize, Deserialize)]
   pub struct MyTool {
       pub param1: String,
       pub param2: Option<u64>,
   }

   impl MyTool {
       pub fn tool_definition() -> Tool {
           Tool {
               name: "my_tool".to_string(),
               description: Some("Description of my tool".to_string()),
               input_schema: serde_json::json!({
                   "type": "object",
                   "properties": {
                       "param1": {"type": "string"},
                       "param2": {"type": "number"}
                   },
                   "required": ["param1"]
               }),
           }
       }

       pub async fn run_tool(
           self,
           fs_service: &FileSystemService
       ) -> Result<CallToolResult, CallToolError> {
           // Your tool logic here
           // Use fs_service.validate_path() for path validation

           Ok(CallToolResult {
               content: vec![Content::Text(TextContent {
                   text: format!("Result: {}", self.param1),
               })],
               is_error: Some(false),
           })
       }
   }
   ```

2. **Add to Composite Tool (if applicable):**

   - Add the operation to the appropriate composite tool (e.g.,
     `single_file_operations.rs`)
   - Update the `operation` enum in the composite tool's schema
   - Implement the operation in the composite tool's `run_tool` method

3. **Or Register as Standalone Tool:**

   - Add `pub mod my_tool;` to `src/tools/mod.rs`
   - Add `pub use my_tool::MyTool;` to exports
   - Add `MyTool` variant to `FileSystemTools` enum
   - Add to `FileSystemTools::tools()` method
   - Add match arm in `TryFrom<CallToolParams>` implementation
   - Update `require_write_access()` if tool modifies filesystem

4. **Update Handler:** Add match arm in `handler.rs::handle_call_tool()`:

   ```rust
   FileSystemTools::MyTool(params) => {
       MyTool::run_tool(params, &self.fs_service).await
   }
   ```

5. **Rebuild:**
   ```bash
   cargo build --release
   ```

### Operation Mode System

To add a new operation mode:

1. **Create Composite Tool:** Follow the pattern of existing composite tools
   (e.g., `single_file_operations.rs`)

2. **Register Mode:**

   - Add to `FileSystemTools` enum in `tools/mod.rs`
   - Add tool definition to `FileSystemTools::tools()`
   - Add match arm in `TryFrom` implementation

3. **Add Mode Mapping:** Update `task_state.rs::get_operation_mode_tools()` to
   return tools for your mode

4. **Update Handler:** Add match arm in `handler.rs::handle_call_tool()`

### Testing

```bash
# Run all tests
cargo test

# Run specific test
cargo test test_name

# Run with output
cargo test -- --nocapture

# Run integration tests
cargo test --test integration_test
```

### Code Quality

```bash
# Format code
cargo fmt

# Lint code
cargo clippy

# Lint with all warnings
cargo clippy -- -W clippy::all

# Check without building
cargo check
```

## Architecture Details

### Tool Organization

Tools are organized into **composite tools** that group related operations:

- **Composite Tools**: High-level tools that route to specific operations
- **Individual Tools**: Low-level implementations (kept for code organization)
- **Operation Modes**: Context-aware tool availability via mode management

### Security Implementation

- **Path Validation**: All paths validated through
  `FileSystemService::validate_path()`
- **Blocklist Check**: Blocked directories checked first (fail-fast)
- **Allowlist Check**: If allowlist specified, path must be within allowed
  directories
- **Path Normalization**: Paths normalized to prevent traversal attacks
- **Home Expansion**: `~` expanded to home directory

### Error Handling

- **ServiceResult**: Custom result type for filesystem operations
- **CallToolError**: MCP-specific error type with proper JSON-RPC formatting
- **Comprehensive Errors**: Detailed error messages for debugging

### Async Operations

- **Tokio Runtime**: Full async/await support via Tokio
- **Non-Blocking I/O**: All filesystem operations are async
- **Concurrent Operations**: Multiple operations can run concurrently

## Troubleshooting

### Server Won't Start

1. **Check Rust Installation:**

   ```bash
   rustc --version  # Should be 1.70+
   cargo --version
   ```

2. **Verify Build:**

   ```bash
   cargo build --release
   ```

3. **Check Executable:** Ensure `target/release/aichemistforge-mcp-server.exe`
   exists

### Permission Errors

- **Windows**: Run as administrator if accessing protected directories
- **Path Validation**: Check that paths aren't in blocked directories
- **Allowlist**: If using allowlist, ensure paths are within allowed directories

### Tools Not Available

- **Operation Mode**: Some tools require specific operation modes to be active
- **Tool Discovery**: Check MCP client logs for tool discovery errors
- **Handler Registration**: Verify tool is registered in `handler.rs`

### Build Issues

- **Dependencies**: Run `cargo update` to update dependencies
- **Clean Build**: Try `cargo clean && cargo build --release`
- **Toolchain**: Ensure Rust toolchain is up to date: `rustup update`

## License

This project is licensed under the MIT License. Refer to the `LICENSE` file in
the project root for details.

## Acknowledgments

- Built with [`rust-mcp-sdk`](https://github.com/modelcontextprotocol/rust-sdk)
  (v0.7)
- Inspired by `@modelcontextprotocol/server-filesystem`
- Utilizes Rust's async ecosystem (Tokio, async-trait)
- File operations powered by `walkdir`, `glob`, `ignore`, `similar`

## Contributing

When contributing:

1. **Follow Rust Conventions**: Use `cargo fmt` and `cargo clippy`
2. **Add Tests**: Include tests for new tools/features
3. **Update Documentation**: Update this README for new tools
4. **Error Handling**: Use proper error types (`ServiceError`, `CallToolError`)
5. **Path Validation**: Always use `fs_service.validate_path()` for path
   operations
6. **Operation Modes**: Consider if new tools should be part of an operation
   mode
