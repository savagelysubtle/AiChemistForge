@echo off
echo Starting Rust MCP Server with HTTP Support via mcp-proxy...
echo.
echo Server will be available at: http://localhost:9877/sse
echo.

cd /d "%~dp0"

REM Build the Rust server first
echo Building Rust server...
cargo build --release
if %errorlevel% neq 0 (
    echo [ERROR] Build failed. Please fix errors and try again.
    pause
    exit /b 1
)

REM Start mcp-proxy in SSE to stdio mode
REM This will expose the stdio-based Rust server over HTTP/SSE
echo Starting mcp-proxy to bridge stdio to HTTP...
mcp-proxy --sse-port 9877 --sse-host 0.0.0.0 --allow-origin="*" -- target\release\rust-mcp-filesystem.exe

pause