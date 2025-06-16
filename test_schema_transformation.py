#!/usr/bin/env python3
"""Test schema transformation for tools."""

import asyncio
import httpx
import json

async def test_schema_transformation():
    """Test that tool schemas are properly transformed."""
    
    # First get tools list
    async with httpx.AsyncClient() as client:
        # Initialize session
        init_response = await client.post(
            "http://localhost:8000/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                },
                "id": 1
            }
        )
        
        print("Initialize response:", init_response.status_code)
        print(json.dumps(init_response.json(), indent=2))
        
        # Get tools list (no auth required for testing)
        tools_response = await client.post(
            "http://localhost:8000/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 2
            }
        )
        
        print("\nTools list response:", tools_response.status_code)
        tools_data = tools_response.json()
        
        if tools_response.status_code != 200:
            print("Error:", json.dumps(tools_data, indent=2))
            print("\nNote: Tools list requires authentication. Testing with direct import instead...")
            
            # Import and test directly
            import sys
            sys.path.insert(0, 'src')
            from telnyx_mcp_server.remote.server import telnyx_mcp_server
            
            # Initialize tools
            await telnyx_mcp_server.initialize_tools()
            
            # Test transformation
            tools_to_check = ["send_message", "get_message", "list_phone_numbers", "get_assistant", "start_assistant_call"]
            
            for tool_name in tools_to_check:
                if tool_name in telnyx_mcp_server.tools:
                    original = telnyx_mcp_server.tools[tool_name]
                    transformed = telnyx_mcp_server._transform_tool_schema(original)
                    print(f"\n{tool_name} - Original schema:")
                    print(json.dumps(original["inputSchema"], indent=2))
                    print(f"\n{tool_name} - Transformed schema:")
                    print(json.dumps(transformed["inputSchema"], indent=2))
        else:
            # Check a few specific tools
            tools_to_check = ["send_message", "get_message", "list_phone_numbers", "get_assistant", "start_assistant_call"]
            
            for tool_name in tools_to_check:
                tool = next((t for t in tools_data["result"]["tools"] if t["name"] == tool_name), None)
                if tool:
                    print(f"\n{tool_name} schema:")
                    print(json.dumps(tool["inputSchema"], indent=2))
                else:
                    print(f"\n{tool_name} not found")

if __name__ == "__main__":
    asyncio.run(test_schema_transformation())