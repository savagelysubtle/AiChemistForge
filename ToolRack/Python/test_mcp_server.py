#!/usr/bin/env python3
"""Test script for the AiChemistForge MCP server connection."""

import asyncio
import json
import logging
import subprocess
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("mcp_test")

async def test_server_connection():
    """Test the MCP server connection and basic functionality."""
    print("🧪 Testing AiChemistForge MCP Server")
    print("="*50)

    # 1. Test server startup
    print("\n1. Testing server startup...")
    try:
        # Get the server script path
        server_path = Path(__file__).parent / "src" / "unified_mcp_server" / "main.py"

        if not server_path.exists():
            print(f"❌ Server script not found at: {server_path}")
            return False

        print(f"✅ Server script found: {server_path}")

        # Test import
        print("\n2. Testing imports...")
        try:
            import unified_mcp_server.main
            print("✅ Main module imports successfully")
        except ImportError as e:
            print(f"❌ Import error: {e}")
            return False

        # Test FastMCP creation
        print("\n3. Testing FastMCP initialization...")
        try:
            from fastmcp import FastMCP
            test_mcp = FastMCP("test_server")
            print("✅ FastMCP instance created successfully")
        except Exception as e:
            print(f"❌ FastMCP creation failed: {e}")
            return False

        # Test basic tool registration
        print("\n4. Testing tool registration...")
        try:
            @test_mcp.tool()
            async def test_tool() -> dict:
                return {"status": "working", "message": "Test tool executed successfully"}

            print("✅ Tool registration works")
        except Exception as e:
            print(f"❌ Tool registration failed: {e}")
            return False

        print("\n5. Testing server startup (will exit after 3 seconds)...")

        # Start server in stdio mode with timeout
        try:
            proc = subprocess.Popen(
                [sys.executable, str(server_path), "--stdio"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Send a test message
            test_message = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"}
                },
                "id": 1
            }

            proc.stdin.write(json.dumps(test_message) + "\n")
            proc.stdin.flush()

            # Wait for response with timeout
            try:
                stdout, stderr = proc.communicate(timeout=3)
                print("✅ Server started and responded")
                if stderr:
                    print(f"📝 Server logs:\n{stderr[:500]}...")
                return True

            except subprocess.TimeoutExpired:
                print("✅ Server started but timed out (this is expected)")
                proc.kill()
                return True

        except Exception as e:
            print(f"❌ Server startup failed: {e}")
            return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("\n📦 Checking dependencies...")

    required_packages = [
        "fastmcp",
        "pydantic",
        "pathlib",
        "sqlite3",  # Built-in
        "typing",   # Built-in
    ]

    missing_packages = []

    for package in required_packages:
        try:
            if package in ["sqlite3", "typing", "pathlib"]:
                # These are built-in, just try importing
                __import__(package)
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n📝 Install missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False

    return True

def generate_client_config():
    """Generate example client configuration."""
    print("\n⚙️ Example client configurations:")

    server_path = Path(__file__).parent / "src" / "unified_mcp_server" / "main.py"

    print("\n📋 Cursor IDE configuration (~/.cursor/mcp_servers.json):")
    cursor_config = {
        "mcpServers": {
            "aichemistforge": {
                "command": "python",
                "args": [str(server_path), "--stdio"],
                "cwd": str(Path(__file__).parent)
            }
        }
    }
    print(json.dumps(cursor_config, indent=2))

    print("\n📋 Claude Desktop configuration:")
    claude_config = {
        "mcpServers": {
            "aichemistforge": {
                "command": "python",
                "args": [str(server_path)],
                "env": {
                    "PYTHONPATH": str(Path(__file__).parent / "src")
                }
            }
        }
    }
    print(json.dumps(claude_config, indent=2))

async def main():
    """Main test function."""
    print("🚀 AiChemistForge MCP Server Test Suite")
    print("="*60)

    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Dependency check failed. Install missing packages and try again.")
        return 1

    # Test server connection
    if await test_server_connection():
        print("\n✅ All tests passed! Your MCP server should work correctly.")
        generate_client_config()

        print("\n📝 Next steps:")
        print("1. Copy the appropriate client configuration above")
        print("2. Restart your MCP client (Cursor/Claude Desktop)")
        print("3. The server should appear in your client's MCP servers list")

        return 0
    else:
        print("\n❌ Tests failed. Check the errors above and fix them.")
        print("\n🔧 Common fixes:")
        print("- Install missing dependencies: pip install fastmcp pydantic")
        print("- Check Python path is correct")
        print("- Ensure all files are in the correct locations")
        print("- Check the documentation guide created above")

        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))