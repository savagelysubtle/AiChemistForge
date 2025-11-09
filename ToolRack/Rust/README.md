<p align="center">
  <img width="128" src="./docs/_media/rust-mcp-filesystem.png" alt="Rust MCP Filesystem Logo">
</p>

# AiChemistForge - Rust Filesystem MCP Server

This Rust MCP (Model Context Protocol) server provides a suite of high-performance, asynchronous tools for filesystem operations. It is designed for efficiency, safety, and robust interaction with the file system. While part of the larger AiChemistForge project, this server can be compiled, run, and utilized as a standalone component.

It serves as a Rust-based alternative and enhancement to filesystem servers typically found in Node.js or other environments, leveraging Rust's strengths in speed, memory safety, and concurrency.

Refer to the [online project documentation](https://rust-mcp-stack.github.io/rust-mcp-filesystem) for more general information about the original `rust-mcp-filesystem` project that this server is based on.

## Features

- **⚡ High Performance**: Built with Rust and Tokio for asynchronous, non-blocking I/O, ensuring efficient handling of filesystem tasks.
- **🔒 Security Conscious**: Operates with a configurable allow-list for accessible directory paths and blocklist for forbidden directories.
- **🚫 Blocklist Support**: Enhanced security model with support for blocking specific directories while allowing others.
- **✍️ Read-Write Mode**: The server operates in read-write mode by default with no read-only option.
- **Advanced Glob Searching**: Powerful file and directory searching using glob patterns.
- **Comprehensive Filesystem Operations**: Offers a wide range of tools for file/directory manipulation, reading, writing, and metadata retrieval.
- **Standalone Binary**: Compiles to a single native executable with no external runtime dependencies (like Node.js or Python), making deployment straightforward.
- **Lightweight**: Minimal resource footprint, suitable for various deployment scenarios.

## Available Tools

This server exposes a rich set of filesystem tools. Based on `src/tools.rs`, the available tools include:

- **`read_file`**: Reads the content of a single text file.
- **`create_directory`**: Creates a new directory, including parent directories if needed.
- **`directory_tree`**: Generates a recursive tree view of a directory's contents.
- **`edit_file`**: Performs line-based edits on a text file.
- **`get_file_info`**: Retrieves detailed metadata for a file or directory.
- **`list_allowed_directories`**: Lists the base directory paths the server is permitted to access.
- **`list_directory`**: Provides a listing of files and subdirectories within a specified directory.
- **`move_file`**: Moves or renames a file or directory.
- **`read_multiple_files`**: Reads the content of multiple text files.
- **`search_files`**: Recursively searches for files and directories matching a glob pattern.
- **`write_file`**: Writes content to a file, creating or overwriting it.
- **`zip_files`**: Compresses specified files into a ZIP archive.
- **`unzip_file`**: Decompresses a ZIP archive.
- **`zip_directory`**: Compresses an entire directory into a ZIP archive.

Each tool has specific input parameters and output formats, adhering to MCP standards. The `require_write_access()` method in `tools.rs` indicates which tools perform modifying operations.

## Installation & Building

### Prerequisites

- **Rust Toolchain**: Ensure you have Rust installed (typically via [rustup](https://rustup.rs/)). This will include `cargo`, the Rust package manager and build tool.
- **Windows**: This project uses batch scripts for Windows. For Linux/Mac, you'll need to create equivalent shell scripts.

### Quick Start (Windows)

1. **Verify Setup:**
   ```batch
   cd AiChemistForge/ToolRack/Rust
   check_setup.bat
   ```

2. **Build the Server (One-time or when code changes):**
   ```batch
   build_mcp_server.bat
   ```
   This creates a release build at `target/release/aichemistforge-mcp-server.exe`

3. **Run the Server:**
   ```batch
   start_mcp_server.bat
   ```
   This runs the pre-built executable (no rebuild)

### Building the Server

**Important:** Build and run are now separated for faster startup:

- **`build_mcp_server.bat`** - Run when you change code (compiles to release binary)
- **`start_mcp_server.bat`** - Run to start server (uses pre-built binary, no rebuild)

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

Once built, you can run the server executable directly from the `target` directory or by using `cargo run`:

```bash
# Using cargo run (from the ToolRack/Rust/ directory)
cargo run --manifest-path ./Cargo.toml -- [--blocked-directories BLOCKED_DIR1 BLOCKED_DIR2] [ALLOWED_PATH_1] [ALLOWED_PATH_2] ...
```

**Explanation of Arguments:**

- `--manifest-path ./Cargo.toml`: Specifies the project's manifest file.
- `--`: Separates `cargo run` options from the arguments passed to the server binary itself.
- `--blocked-directories DIR1,DIR2,DIR3` (Optional): A **comma-separated** list of directory paths that are blocked from access. These directories will be inaccessible regardless of the allowed directories. When using the batch file launcher, default system directories are automatically blocked from `forbidden_dirs.txt`.
- `[ALLOWED_PATH_1] [ALLOWED_PATH_2] ...`: A space-separated list of absolute directory paths that are permitted for operation. If no allowed paths are specified, the server operates in unrestricted mode (all directories allowed except blocked ones).

## Two-Tier Blocklist Architecture

The server implements a **two-tier blocklist system** for enhanced security:

### Tier 1: Default Blocklist (Automatic)

When using `start_mcp_server.bat`, the server automatically blocks system-critical directories from `forbidden_dirs.txt`:

- `C:\Windows`
- `C:\Program Files`
- `C:\Program Files (x86)`
- `C:\ProgramData`
- Additional directories as configured

These default blocks are **always applied** and protect sensitive system directories.

### Tier 2: Custom Blocklist (Optional)

You can add additional blocked directories via:

1. **Command line**: `--blocked-directories "D:\Sensitive,C:\Private"`
2. **MCP JSON config** (`.gemini/settings.json`):

```json
"Rust": {
  "command": "D:\\Path\\To\\start_mcp_server.bat",
  "args": ["--blocked-directories", "D:\\SensitiveProject,C:\\PrivateData"],
  "type": "stdio",
  "env": {
    "RUST_LOG": "debug",
    "TRUST": "true"
  }
}
```

The server merges both tiers into a single blocklist, ensuring maximum protection.

**Example 1 - Unrestricted read-write mode with blocklist:**
To run the server in unrestricted read-write mode but block access to system directories:

```bash
cargo run --manifest-path ./Cargo.toml -- --blocked-directories "C:\Windows,C:\Program Files"
```

**Example 2 - Restricted read-write mode with allowed directories:**
To run the server allowing access to specific directories:

```bash
cargo run --manifest-path ./Cargo.toml -- /home/user/project1 /home/user/project2
```

### Using the `mcp_rust_tool.bat` (Windows, with MCP Inspector)

The provided `mcp_rust_tool.bat` script demonstrates running the server with the `@modelcontextprotocol/inspector` and `uv` for a more integrated development/testing experience.

```batch
@echo off
setlocal

set "RUST_LOG=debug"

REM The npx command invokes the MCP inspector, which then runs the Rust server via uv and cargo.
npx @modelcontextprotocol/inspector ^
  uv ^
  --directory "D:/Coding/AiChemistCodex/AiChemistForge/ToolRack/Rust/" ^
  run cargo ^
  run ^
  --manifest-path "D:/Coding/AiChemistCodex/AiChemistForge/ToolRack/Rust/Cargo.toml" ^
  -- ^
  --blocked-directories "C:/Windows" "C:/Program Files" ^
  "D:/Coding/AiChemistCodex/AiChemistForge/ToolRack/Rust/test_files" ^
  "F:/" ^
  "D:/"

endlocal
```

**Key aspects of the batch file:**

- Sets `RUST_LOG=debug` for verbose logging from the Rust application.
- Uses `npx` to run the MCP inspector.
- The inspector is configured to use `uv` to execute `cargo run`.
- `--directory` specifies the working directory for `uv`.
- The arguments after `--` are passed to the Rust MCP server binary, including `--blocked-directories` and the allowed paths.

**To use this batch file:**

1. Ensure Node.js (for `npx`) and `uv` are installed and in your PATH.
2. Update the absolute paths within the batch file if your AiChemistForge project is located elsewhere.
3. Run `mcp_rust_tool.bat` from your command prompt.

### Connecting from an MCP Client (e.g., Cursor)

To connect this Rust MCP server to Cursor IDE:

1. **The MCP configuration is already set up** in `.cursor/mcp.json` at the repository root:

```json
{
  "mcpServers": {
    "Rust": {
      "command": "D:\\Coding\\AiChemistCodex\\AiChemistForge\\ToolRack\\Rust\\start_mcp_server.bat",
      "args": [],
      "type": "stdio",
      "env": {
        "RUST_LOG": "info"
      }
    }
  }
}
```

2. **Build the server first:**
   ```batch
   cd ToolRack/Rust
   build_mcp_server.bat
   ```

3. **Restart Cursor** to load the MCP server configuration

4. **Verify connection:**
   - Open Cursor's command palette (Ctrl+Shift+P)
   - Search for "MCP" commands
   - You should see the Rust server listed

**Adding Custom Blocked Directories:**

If you need to block additional directories beyond the defaults, add them to the `args` array:

```json
{
  "mcpServers": {
    "Rust": {
      "command": "D:\\Coding\\AiChemistCodex\\AiChemistForge\\ToolRack\\Rust\\start_mcp_server.bat",
      "args": ["--blocked-directories", "D:\\SensitiveProject,C:\\PrivateData"],
      "type": "stdio",
      "env": {
        "RUST_LOG": "info"
      }
    }
  }
}
```

## Development

### Project Structure

Key files and directories within `ToolRack/Rust/`:

- `Cargo.toml`: The Rust project manifest, defining dependencies and project metadata.
- `src/`: Contains the Rust source code.
  - `main.rs`: The main entry point for the server application.
  - `tools.rs`: Defines the `FileSystemTools` enum, tool registration (`tool_box!`), and the `require_write_access` logic. It imports individual tool modules.
  - `tools/`: A directory containing modules for each specific tool (e.g., `create_directory.rs`, `read_files.rs`).
- `docs/_media/`: Contains media like logos.
- `tests/`: Contains integration or unit tests for the server and its tools.
- `mcp_rust_tool.bat` (in parent `AiChemistForge` dir): Example batch script to run the server with an inspector.

### Adding New Tools

1. **Create a New Tool Module:**
    In the `src/tools/` directory, create a new Rust file (e.g., `my_new_tool.rs`).
    Implement the tool logic, typically by defining a struct and implementing the `rust_mcp_sdk::Tool` trait (or by following the pattern of existing tools if they use a different abstraction provided by `rust-mcp-sdk`).

    ```rust
    // Example structure (may vary based on rust-mcp-sdk specifics)
    use rust_mcp_sdk::mcp_tool_frontend; // or similar macros/traits
    use serde::{Deserialize, Serialize};

    #[derive(Deserialize, Debug)] // For input parameters
    pub struct MyNewToolParams {
        pub example_param: String,
    }

    #[derive(Serialize, Debug)] // For tool output
    pub struct MyNewToolResult {
        pub message: String,
    }

    mcp_tool_frontend! {
        MyNewTool, // Tool name
        "A description of my new tool.", // Tool description
        MyNewToolParams, // Input parameter type
        MyNewToolResult // Output type
    }

    impl MyNewTool {
        pub async fn run(params: MyNewToolParams) -> Result<MyNewToolResult, anyhow::Error> {
            // Your tool logic here
            Ok(MyNewToolResult {
                message: format!("Processed: {}", params.example_param),
            })
        }
    }
    ```

2. **Register the Tool in `tools.rs`:**
    - Add `mod my_new_tool;` at the top of `src/tools.rs`.
    - Add `pub use my_new_tool::MyNewToolTool;` (or the appropriate generated name) to the `pub use` statements.
    - Include `MyNewToolTool` in the `tool_box!` macro invocation.
    - Update the `require_write_access` match statement if your new tool modifies the filesystem.

3. **Rebuild:**
    Run `cargo build` or `cargo run` to compile the changes.

## License

This project is typically licensed under an open-source license (e.g., MIT). Refer to the `LICENSE` file in the root of the AiChemistForge repository for specific details.

## Acknowledgments

- Inspired by `@modelcontextprotocol/server-filesystem`.
- Built with the robust `rust-mcp-sdk` and `rust-mcp-schema`.
- Utilizes the power of the Rust programming language and its ecosystem.
