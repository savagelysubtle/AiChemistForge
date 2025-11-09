@echo off
echo Starting TypeScript MCP Server with HTTP Support via mcp-proxy...
echo.
echo Server will be available at: http://localhost:9878/sse
echo.

cd /d "%~dp0"

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Please install Node.js first.
    pause
    exit /b 1
)

REM Check if dist directory exists
if not exist "dist\index.js" (
    echo [ERROR] Compiled JavaScript not found. Running build...
    call npm run build
    if %errorlevel% neq 0 (
        echo [ERROR] Build failed. Please fix errors and try again.
        pause
        exit /b 1
    )
)

REM Start mcp-proxy in SSE to stdio mode
REM This will expose the stdio-based TypeScript server over HTTP/SSE
echo Starting mcp-proxy to bridge stdio to HTTP...
mcp-proxy --sse-port 9878 --sse-host 0.0.0.0 --allow-origin="*" -- node dist\index.js

pause