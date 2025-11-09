@echo off
REM AiChemistForge Rust MCP Server Builder
REM Run this script when you make code changes

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%"

REM Change to the project directory
cd /d "%PROJECT_ROOT%"

echo ========================================
echo Building AiChemistForge Rust MCP Server
echo ========================================
echo.

REM Check if cargo is available
where cargo >nul 2>nul
if errorlevel 1 (
    echo ERROR: Cargo not found in PATH
    echo Please install Rust from https://rustup.rs/
    pause
    exit /b 1
)

REM Build the release version
echo Building release version...
cargo build --release --quiet

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build complete!
echo ========================================
echo Binary location: target\release\aichemistforge-mcp-server.exe
echo Size:
dir "target\release\aichemistforge-mcp-server.exe" | findstr "aichemistforge-mcp-server.exe"
echo.
echo You can now start the server with start_mcp_server.bat
pause

