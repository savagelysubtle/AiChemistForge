@echo off
REM AiChemistForge Rust MCP Server Launcher
REM New security model: Allow everything except blocked folders, with optional allowlist
REM Blocked folders are read from forbidden_dirs.txt in the project root

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%"

REM Change to the project directory
cd /d "%PROJECT_ROOT%"

REM Set up Rust environment
set "RUST_LOG=warn"

REM Display startup message (to stderr to avoid JSON-RPC interference)
echo Starting AiChemistForge Rust MCP Server with stdio transport... >&2
echo Logs will appear on stderr, JSON-RPC communication on stdout >&2

REM Initialize default settings
set "BLOCKED_DIRS_FLAG=--blocked-directories"
set "DEFAULT_BLOCKED_DIRS="
set "EXTRA_BLOCKED_DIRS="

REM Read default blocked directories from file
if exist "forbidden_dirs.txt" (
    for /f "usebackq tokens=*" %%i in (`findstr /r /c:"^[^#]" forbidden_dirs.txt`) do (
        if "%%i" neq "" (
            if defined DEFAULT_BLOCKED_DIRS (
                set "DEFAULT_BLOCKED_DIRS=!DEFAULT_BLOCKED_DIRS!,%%i"
            ) else (
                set "DEFAULT_BLOCKED_DIRS=%%i"
            )
        )
    )
) else (
    REM Default blocked directories - system directories for security
    set "DEFAULT_BLOCKED_DIRS=C:\Windows,C:\Program Files,C:\Program Files (x86)"
)

REM Parse command-line arguments for additional blocked directories
:parse_args
if "%~1"=="" goto merge_blocked_dirs
if "%~1"=="--debug" (
    set "RUST_LOG=debug"
    shift
    goto parse_args
)
if "%~1"=="--blocked-directories" (
    shift
    set "EXTRA_BLOCKED_DIRS=%~1"
    shift
    goto parse_args
)
REM Ignore any other arguments
shift
goto parse_args

:merge_blocked_dirs
REM Merge default and extra blocked directories
if defined EXTRA_BLOCKED_DIRS (
    set "BLOCKED_DIRS=!DEFAULT_BLOCKED_DIRS!,!EXTRA_BLOCKED_DIRS!"
) else (
    set "BLOCKED_DIRS=!DEFAULT_BLOCKED_DIRS!"
)

:run_server
REM Check if the executable exists
if not exist "target\release\aichemistforge-mcp-server.exe" (
    echo ERROR: Server executable not found! >&2
    echo Please run build_mcp_server.bat first to compile the server. >&2
    echo Or run: cargo build --release >&2
    exit /b 1
)

REM Start the server with blocked directories
echo MCP Server listening on stdin/stdout... >&2
echo Security model: Allow all directories except blocked folders >&2
echo Mode: READ-WRITE >&2
echo ---------------------------------------- >&2
echo Default blocked directories: !DEFAULT_BLOCKED_DIRS! >&2
if defined EXTRA_BLOCKED_DIRS (
    echo Additional blocked directories: !EXTRA_BLOCKED_DIRS! >&2
    echo Merged blocklist: !BLOCKED_DIRS! >&2
) else (
    echo No additional blocked directories specified >&2
)
echo ---------------------------------------- >&2
echo Starting server... >&2

REM Run the pre-built executable directly (no rebuild)
target\release\aichemistforge-mcp-server.exe !BLOCKED_DIRS_FLAG! "!BLOCKED_DIRS!"