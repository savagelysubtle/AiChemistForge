@echo off
echo Starting AiChemistForge MCP Server with Streamable HTTP Transport...
echo.
echo Server will be available at: http://localhost:9876/mcp
echo.

cd /d "%~dp0"

REM Start the server with HTTP transport using uv
uv run python -m unified_mcp_server.main --http --host 0.0.0.0 --port 9876

pause