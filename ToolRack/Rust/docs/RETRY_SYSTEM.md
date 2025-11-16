# Retry System for Rust MCP Server

## Overview

The Rust MCP server now includes an automatic retry system similar to the Python server, providing robust error handling with configurable backoff strategies for transient errors in filesystem operations.

## Features

- **Smart Retry Logic**: Automatically retries operations on transient I/O errors
- **Configurable Backoff**: Exponential, Linear, and Fixed backoff strategies
- **Error Classification**: Distinguishes between retryable (transient) and non-retryable (permanent) errors
- **Comprehensive Logging**: All retry attempts logged for debugging
- **Zero Overhead**: No performance impact on successful operations
- **Type-Safe**: Leverages Rust's type system for compile-time safety

## Retry Configuration

### RetryConfig

```rust
use aichemistforge_mcp_server::retry::{RetryConfig, RetryStrategy};

// Default configuration (3 attempts, exponential backoff)
let config = RetryConfig::default();

// Custom configuration
let config = RetryConfig::new()
    .with_max_attempts(5)
    .with_initial_delay_ms(2000)
    .with_max_delay_ms(60000)
    .with_strategy(RetryStrategy::Exponential)
    .with_backoff_multiplier(2.0);
```

### Retry Strategies

#### Exponential Backoff (Default)
```rust
RetryStrategy::Exponential
// Delay: 1s, 2s, 4s, 8s, 16s...
```

#### Linear Backoff
```rust
RetryStrategy::Linear
// Delay: 1s, 2s, 3s, 4s, 5s...
```

#### Fixed Backoff
```rust
RetryStrategy::Fixed
// Delay: 1s, 1s, 1s, 1s, 1s...
```

## Usage

### Simple Retry (3 attempts)

```rust
use aichemistforge_mcp_server::retry::retry_3x;

async fn read_file_with_retry(path: &Path, fs_service: &FileSystemService) -> Result<String, ServiceError> {
    retry_3x("read_file", async {
        fs_service.read_file(path).await
    }).await
}
```

### I/O-Specific Retry

```rust
use aichemistforge_mcp_server::retry::retry_io_operation;

async fn write_file_with_retry(path: &Path, content: &str, fs_service: &FileSystemService) -> Result<(), ServiceError> {
    retry_io_operation("write_file", async {
        fs_service.write_file(path, content).await
    }).await
}
```

### Advanced Configuration

```rust
use aichemistforge_mcp_server::retry::{retry_with_config, RetryConfig, RetryStrategy};

async fn complex_operation() -> Result<String, ServiceError> {
    let config = RetryConfig::new()
        .with_max_attempts(5)
        .with_initial_delay_ms(2000)
        .with_strategy(RetryStrategy::Linear);

    retry_with_config("complex_op", async {
        // Your operation here
        Ok("success".to_string())
    }, &config).await
}
```

### Using the Macro

```rust
use aichemistforge_mcp_server::retry_async;

let result = retry_async!("my_tool", 3, {
    fs_service.read_file(path).await
});
```

## Applied to Tools

The retry logic is currently applied to these critical filesystem tools:

### Tools with Retry

- **`read_file`**: Retries on I/O errors (3 attempts, exponential backoff)
- **`write_file`**: Retries on I/O errors (3 attempts, exponential backoff)
- **`directory_tree`**: Retries on I/O errors (3 attempts, exponential backoff)
- **`list_directory`**: Retries on I/O errors (3 attempts, exponential backoff)

### Example: read_file Tool

```rust
use crate::retry::retry_3x;

pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
    // Retry up to 3 times on transient I/O errors
    match retry_3x("read_file", async {
        fs_service.read_file(Path::new(&self.path)).await
    }).await {
        Ok(content) => Ok(CallToolResult {
            content: vec![Content::Text(TextContent {
                text: content,
            })],
            is_error: Some(false),
        }),
        Err(e) => Err(CallToolError::new(e)),
    }
}
```

## Error Classification

### Retryable Errors (Transient)

These `std::io::ErrorKind` variants trigger automatic retries:

- `PermissionDenied` - Temporary file lock
- `ConnectionRefused` - Network might recover
- `ConnectionReset` - Network disconnection
- `ConnectionAborted` - Connection interrupted
- `NotConnected` - Network temporarily unavailable
- `AddrInUse` - Address temporarily in use
- `AddrNotAvailable` - Address temporarily unavailable
- `BrokenPipe` - Pipe might recover
- `WouldBlock` - Resource temporarily unavailable
- `TimedOut` - Timeout might recover on retry
- `WriteZero` - Write buffer issue
- `Interrupted` - System call interrupted
- `Other` - Unknown I/O errors (default to retry)

### Non-Retryable Errors (Permanent)

These errors do NOT trigger retries:

- `NotFound` - File doesn't exist (won't change)
- `AlreadyExists` - File exists (won't change)
- `InvalidInput` - Invalid parameters
- `InvalidData` - Corrupted data
- `Unsupported` - Operation not supported
- `UnexpectedEof` - Unexpected end of file
- `OutOfMemory` - Memory exhaustion
- `PathNotAllowed` - Security violation
- `DirectoryAlreadyExists` - Directory exists
- `FileNotFound` - File doesn't exist
- `InvalidMediaFile` - Invalid file format
- `ContentSearchError` - Regex pattern error

## Logging

The retry system logs all retry attempts for debugging:

```
WARN Tool 'read_file' failed on attempt 1/3: Permission denied. Retrying in 1s...
WARN Tool 'read_file' failed on attempt 2/3: Permission denied. Retrying in 2s...
INFO Tool 'read_file' succeeded on attempt 3/3
```

Or if all retries fail:

```
WARN Tool 'read_file' failed on attempt 1/3: Permission denied. Retrying in 1s...
WARN Tool 'read_file' failed on attempt 2/3: Permission denied. Retrying in 2s...
ERROR Tool 'read_file' failed after 3 attempts
```

## Testing

The retry module includes comprehensive unit tests:

```bash
# Run retry tests
cd ToolRack/Rust
cargo test retry

# Run all tests
cargo test

# Run with output
cargo test retry -- --nocapture
```

### Test Coverage

- ✅ Default configuration values
- ✅ Exponential backoff calculation
- ✅ Linear backoff calculation
- ✅ Fixed backoff calculation
- ✅ Max delay cap enforcement
- ✅ Error classification (retryable vs non-retryable)
- ✅ Success on first attempt
- ✅ Success after retries
- ✅ Failure after max attempts

## Building

To build the Rust server with retry functionality:

```bash
cd ToolRack/Rust

# Build release version
cargo build --release

# Or use the build script
.\build_mcp_server.bat
```

## Adding Retry to New Tools

To add retry logic to a new tool:

```rust
use crate::retry::retry_3x;  // Add this import

impl MyNewTool {
    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        // Wrap your operation with retry_3x
        match retry_3x("my_new_tool", async {
            fs_service.my_operation(/* params */).await
        }).await {
            Ok(result) => {
                // Handle success
                Ok(CallToolResult { /* ... */ })
            },
            Err(e) => Err(CallToolError::new(e)),
        }
    }
}
```

## Best Practices

### When to Use Retry

✅ **Use retry for**:
- File read/write operations
- Directory listings
- File metadata queries
- Network filesystem operations
- Database connections (future)

❌ **Don't use retry for**:
- Input validation
- Path security checks
- Permission denied (security)
- File format validation

### Choosing Retry Strategy

- **Exponential**: Network operations, external APIs
- **Linear**: Filesystem operations, local I/O
- **Fixed**: Simple scenarios, quick retries

### Choosing Max Attempts

- **3 attempts**: Default for most tools
- **5 attempts**: Network operations with high latency
- **1 attempt**: No retry (validation/security tools)

## Performance Impact

### Zero Overhead on Success
- Successful operations: **0ms overhead**
- Only failed operations incur retry delays

### Retry Delays

#### Exponential (1s initial):
- Attempt 1: Immediate
- Attempt 2: +1s delay
- Attempt 3: +2s delay
- **Total worst case**: ~3s for 3 attempts

#### Linear (1s initial):
- Attempt 1: Immediate
- Attempt 2: +2s delay
- Attempt 3: +3s delay
- **Total worst case**: ~5s for 3 attempts

## Comparison with Python Server

| Feature | Python | Rust |
|---------|--------|------|
| Retry Strategies | ✅ 3 types | ✅ 3 types |
| Error Classification | ✅ | ✅ |
| Configurable Backoff | ✅ | ✅ |
| Logging | ✅ | ✅ |
| Max Attempts | ✅ Configurable | ✅ Configurable |
| Type Safety | Python types | Rust compile-time |
| Performance | Async/await | Tokio async |

## Future Enhancements

- [ ] Circuit breaker pattern
- [ ] Jitter in backoff (randomize delays)
- [ ] Retry metrics collection
- [ ] Per-tool retry configuration
- [ ] Conditional retry based on error messages
- [ ] Global retry budget limits

## Troubleshooting

### Retry Not Working

**Problem**: Tool doesn't retry on failure

**Solutions**:
1. Check that the error is retryable:
   ```rust
   let config = RetryConfig::default();
   println!("Is retryable: {}", config.is_retryable(&error));
   ```

2. Check logs for retry messages (should appear in stderr)

3. Verify the tool is using `retry_3x` or similar wrapper

### Too Many Retries

**Problem**: Tool retries too many times, causing delays

**Solutions**:
1. Reduce max_attempts:
   ```rust
   let config = RetryConfig::new().with_max_attempts(2);
   retry_with_config("my_tool", operation, &config).await
   ```

2. Make error non-retryable if it's permanent

### Compilation Errors

**Problem**: Rust compiler errors about retry module

**Solutions**:
1. Ensure `src/retry.rs` exists
2. Ensure `lib.rs` includes `pub mod retry;`
3. Run `cargo clean && cargo build`

---

**Version**: 1.0.0
**Last Updated**: 2025-11-12
**Author**: AiChemistForge Team


