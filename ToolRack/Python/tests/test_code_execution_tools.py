#!/usr/bin/env python3
"""Test script for code execution tools."""

import asyncio
import json
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastmcp import Client

from unified_mcp_server.main import mcp


async def test_code_execution_tools():
    """Test all code execution tools."""
    print("🧪 Testing Code Execution Tools")
    print("=" * 60)

    try:
        async with Client(mcp) as client:
            print("✅ Connected to MCP server\n")

            # 1. Test generate_python_tool_apis
            print("1️⃣  Testing generate_python_tool_apis...")
            try:
                result = await client.call_tool(
                    "generate_python_tool_apis",
                    {
                        "output_dir": "./servers/python",
                        "server_name": "python",
                        "regenerate": True,
                    },
                )
                # FastMCP returns result as list of content items
                if result and len(result) > 0:
                    # Try to parse as JSON if it's a string, otherwise use directly
                    result_text = str(result[0].text) if hasattr(result[0], 'text') else str(result[0])
                    try:
                        content = json.loads(result_text)
                    except (json.JSONDecodeError, TypeError):
                        content = result_text if isinstance(result_text, dict) else {"result": result_text}

                    if isinstance(content, dict) and content.get("success"):
                        print(f"   ✅ Generated {content.get('tools_generated')} tool APIs")
                        print(f"   📁 Output: {content.get('output_dir')}")
                        print(f"   📄 Files: {len(content.get('generated_files', []))}")
                    elif isinstance(content, dict) and not content.get("success"):
                        print(f"   ❌ Failed: {content.get('error')}")
                    else:
                        print(f"   ✅ Result: {result_text[:200]}...")
                else:
                    print("   ❌ No result returned")
            except Exception as e:
                print(f"   ❌ Error: {e}")

            print()
            print("🎉 Code execution tools test complete!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    asyncio.run(test_code_execution_tools())

