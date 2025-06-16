#!/usr/bin/env python3
"""Test script for Telnyx Remote MCP Server."""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_server():
    """Test that the remote server can start and tools are loaded."""
    try:
        # Import the server module
        from telnyx_mcp_server.remote.server import app, telnyx_mcp_server
        
        print("✅ Remote server module imported successfully")
        
        # Check that tools are loaded
        num_tools = len(telnyx_mcp_server.tools)
        print(f"✅ Loaded {num_tools} Telnyx tools")
        
        if num_tools > 0:
            print("\nAvailable tools:")
            for tool_name in list(telnyx_mcp_server.tools.keys())[:10]:  # Show first 10
                print(f"  - {tool_name}")
            if num_tools > 10:
                print(f"  ... and {num_tools - 10} more")
        
        print("\n✅ Remote server is ready to run!")
        print("\nTo start the server, run:")
        print("  uvicorn telnyx_mcp_server.remote.server:app --reload --port 8000")
        print("\nThen visit: http://localhost:8000/test-auth")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("TELNYX_API_KEY"):
        print("⚠️  Warning: TELNYX_API_KEY not set. Server will start but tools won't work.")
        print("   Set it in .env or export TELNYX_API_KEY=your-key")
    
    success = asyncio.run(test_server())
    sys.exit(0 if success else 1)