@echo off
REM Windows batch file for starting the TypeScript MCP Server
REM This provides better error handling and environment setup

cd /d "%~dp0"

REM Set environment variables
set NODE_ENV=production
set LOG_LEVEL=INFO
set MCP_SERVER_NAME=TypeScript

REM Enable detailed Node.js diagnostics
set NODE_OPTIONS=--trace-warnings

REM Redirect all output to stderr to keep stdout clean for MCP protocol
echo ===================================== 1>&2
echo  TypeScript MCP Server Startup 1>&2
echo ===================================== 1>&2
echo Current Directory: %CD% 1>&2
echo Node Version: 1>&2
node --version 1>&2
echo. 1>&2

REM Check if dist directory exists
if not exist "dist\server\server.js" (
    echo [ERROR] Compiled JavaScript not found. Please run 'npm run build' first. 1>&2
    echo. 1>&2
    echo To build the project: 1>&2
    echo   npm run build 1>&2
    echo. 1>&2
    pause
    exit /b 1
)

REM Check if node_modules exists
if not exist "node_modules" (
    echo [ERROR] Dependencies not installed. Please run 'npm install' first. 1>&2
    echo. 1>&2
    echo To install dependencies: 1>&2
    echo   npm install 1>&2
    echo. 1>&2
    pause
    exit /b 1
)

echo [INFO] All prerequisites checked - OK 1>&2
echo [INFO] Starting TypeScript MCP Server... 1>&2
echo [INFO] Listening on STDIO for MCP protocol messages 1>&2
echo [INFO] Press Ctrl+C to stop the server 1>&2
echo. 1>&2

REM Start the server with stdout reserved for MCP protocol
node dist\server\server.js

REM Capture exit code
set EXIT_CODE=%ERRORLEVEL%
echo. 1>&2
echo ===================================== 1>&2
echo [INFO] TypeScript MCP Server stopped with exit code: %EXIT_CODE% 1>&2
if %EXIT_CODE% neq 0 (
    echo [ERROR] Server exited with an error 1>&2
    echo [INFO] Check the logs above for error details 1>&2
)
echo ===================================== 1>&2
