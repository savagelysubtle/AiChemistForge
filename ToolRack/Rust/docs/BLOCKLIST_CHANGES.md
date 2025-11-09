# Blocklist Functionality Implementation and Fixes

This document summarizes the changes made to implement blocklist functionality and fix the inverted blocklist bug in the AiChemistForge Rust MCP Filesystem Server.

## Critical Bug Fix (October 2025)

### Issue: Inverted Blocklist Behavior

The original implementation had a critical CLI argument parsing bug that caused blocked directories to be treated as allowed directories and vice versa.

**Root Cause:**

- The `blocked_directories` Vec in `cli.rs` didn't specify it accepts multiple values
- Clap only captured the first value after `--blocked-directories`
- Remaining values became positional arguments going into `allowed_directories`
- Result: Blocked dirs → Allowed list, causing complete inversion

**Fix Applied:**

1. Added `num_args = 0..` and `value_delimiter = ','` to the CLI argument definition
2. Changed from space-separated to comma-separated values
3. Updated batch file to properly format and merge blocklist tiers
4. Implemented two-tier blocklist architecture (default + custom)

## Overview

The original implementation used an allowlist-only security model where:

- By default, the server operated in read-only mode
- Write access required the `--allow-write` flag
- Access was restricted to specified allowed directories

The new implementation uses a more flexible security model with:

- Read-write mode by default with no read-only option
- Support for both allowlist and blocklist approaches
- Unrestricted mode when no allowed directories are specified (except blocked directories)

## Key Changes

### 1. CLI Arguments (`src/cli.rs`)

**Before:**

```rust
#[derive(Parser, Debug)]
#[command(name = env!("CARGO_PKG_NAME"))]
#[command(version = env!("CARGO_PKG_VERSION"))]
pub struct CommandArguments {
    #[arg(short = 'w', long, help = "Enables read/write mode for the app, allowing both reading and writing.")]
    pub allow_write: bool,

    #[arg(help = "List of directories that are forbidden for the operation.")]
    pub allowed_directories: Vec<String>,
}
```

**After:**

```rust
#[derive(Parser, Debug)]
#[command(name = env!("CARGO_PKG_NAME"))]
#[command(version = env!("CARGO_PKG_VERSION"))]
pub struct CommandArguments {
    #[arg(
        long,
        help = "List of directories that are blocked from access.",
        long_help = "Provide a space-separated list of directories that are blocked from operation."
    )]
    pub blocked_directories: Vec<String>,

    #[arg(
        help = "List of directories that are permitted for the operation. Leave empty for unrestricted access (except blocked directories)."
    )]
    pub allowed_directories: Vec<String>,
}
```

### 2. Handler Logic (`src/handler.rs`)

**Before:**

```rust
let fs_service = FileSystemService::try_new(&args.allowed_directories)?;
Ok(Self {
    fs_service,
    readonly: !&args.allow_write,
})
```

**After:**

```rust
let fs_service = FileSystemService::try_new(&args.allowed_directories, &args.blocked_directories)?;
Ok(Self {
    fs_service,
    readonly: false, // Always false for read-write mode
})
```

The `assert_write_access` method now always allows write access since the server is always in read-write mode:

```rust
pub fn assert_write_access(&self) -> std::result::Result<(), CallToolError> {
    // Always allow write access since we're in read-write mode
    Ok(())
}
```

### 3. File System Service (`src/fs_service.rs`)

**Before:**

- Only supported allowlist validation
- Used `forbidden_directories` parameter name but treated as allowlist

**After:**

- Supports both allowlist and blocklist validation
- New validation logic:
  1. Check if path is in blocked directories (deny if found)
  2. If allowed_directories is empty, allow access (unrestricted mode)
  3. Otherwise, check if path is in allowed directories (allow if found, deny otherwise)

### 4. Validation Logic

**New validation flow:**

```rust
pub async fn validate_path(&self, requested_path: &Path) -> ServiceResult<PathBuf> {
    // Expand ~ to home directory
    let expanded_path = expand_home(requested_path.to_path_buf());

    // Resolve the absolute path
    let absolute_path = if expanded_path.as_path().is_absolute() {
        expanded_path.clone()
    } else {
        env::current_dir().unwrap().join(&expanded_path)
    };

    // Normalize the path
    let normalized_requested = normalize_path(&absolute_path);

    // Check if path is in blocked directories first
    if !self.blocked_path.is_empty() {
        for blocked_dir in &self.blocked_path {
            if normalized_requested.starts_with(blocked_dir)
                || normalized_requested.starts_with(&normalize_path(blocked_dir)) {
                return Err(ServiceError::PathNotAllowed);
            }
        }
    }

    // If allowed_directories is empty, allow access (unrestricted mode)
    if self.allowed_path.is_empty() {
        return Ok(absolute_path);
    }

    // Otherwise, check allowlist
    if !self.allowed_path.iter().any(|dir| {
        normalized_requested.starts_with(dir)
            || normalized_requested.starts_with(&normalize_path(dir))
    }) {
        return Err(ServiceError::PathNotAllowed);
    }

    Ok(absolute_path)
}
```

## Two-Tier Blocklist Architecture

### Tier 1: Default Blocklist (Automatic)

The batch file `start_mcp_server.bat` automatically loads blocked directories from `forbidden_dirs.txt`:

- System-critical directories are always blocked
- No user action required
- Provides baseline security

### Tier 2: Custom Blocklist (Optional)

Users can add additional blocked directories via:

- Command-line arguments
- MCP JSON configuration (`.gemini/settings.json`)

**Example MCP Configuration:**

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

## Usage Examples

### 1. Unrestricted Read-Write Mode with Default Blocklist

```bash
# Uses default blocklist from forbidden_dirs.txt
cargo run --manifest-path ./Cargo.toml --
```

### 2. Unrestricted Mode with Custom Blocklist

```bash
# Comma-separated values for multiple directories
cargo run --manifest-path ./Cargo.toml -- --blocked-directories "C:\Windows,C:\Program Files,D:\Sensitive"
```

### 3. Restricted Read-Write Mode

```bash
cargo run --manifest-path ./Cargo.toml -- C:\Users\MyProject C:\Temp
```

## Security Considerations

1. **Default Security**: The server now defaults to read-write mode with no option for read-only mode. This is less secure than the original read-only default but provides more flexibility.

2. **Blocklist Priority**: Blocked directories take precedence over allowed directories. If a path is in both lists, it will be blocked.

3. **Unrestricted Mode**: When no allowed directories are specified, the server operates in unrestricted mode (except for blocked directories). This is more permissive than the original implementation.

4. **Path Normalization**: The implementation uses path normalization to prevent directory traversal attacks.

## Testing

Created test programs to verify functionality:

- `src/bin/test_blocklist.rs`: Tests various combinations of allowed and blocked directories
- `examples/blocklist_example.rs`: Demonstrates usage patterns

## Documentation

Updated `README.md` to document the new CLI arguments and usage patterns.
