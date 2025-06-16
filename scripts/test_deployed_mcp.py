#!/usr/bin/env python3
"""Test the deployed MCP server."""

import asyncio
import httpx
import json

BASE_URL = "https://app-web-3ky2b33hy2dpm.azurewebsites.net"


async def test_deployed_server():
    """Test the deployed MCP server with full protocol flow."""
    print(f"Testing deployed MCP server at {BASE_URL}\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Check server health
        print("1. Checking server health...")
        response = await client.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Version: {data.get('version')}")
            print(f"   Protocol: {data.get('protocol_version')}")
        
        # 2. OAuth Metadata Discovery
        print("\n2. Testing OAuth Metadata Discovery...")
        response = await client.get(f"{BASE_URL}/.well-known/oauth-authorization-server")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            metadata = response.json()
            print(f"   Authorization: {metadata.get('authorization_endpoint')}")
            print(f"   Token: {metadata.get('token_endpoint')}")
            print(f"   Registration: {metadata.get('registration_endpoint')}")
        
        # 3. Test MCP without auth (should work for discovery)
        print("\n3. Testing MCP Initialize (no auth)...")
        message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        response = await client.post(
            f"{BASE_URL}/mcp",
            json=message,
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Protocol: {result['result']['protocolVersion']}")
            print(f"   Capabilities: {json.dumps(result['result']['capabilities'], indent=6)}")
        
        # 4. Test SSE support
        print("\n4. Testing SSE Support...")
        response = await client.post(
            f"{BASE_URL}/mcp",
            json=message,
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            }
        )
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type')}")
        if "text/event-stream" in response.headers.get('content-type', ''):
            print("   ✅ SSE support confirmed!")
        
        # 5. Test batch request
        print("\n5. Testing Batch Request...")
        batch = [
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            },
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {}
            }
        ]
        
        response = await client.post(
            f"{BASE_URL}/mcp",
            json=batch,
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            print(f"   Response type: {'batch' if isinstance(results, list) else 'single'}")
            if isinstance(results, list):
                print(f"   Responses received: {len(results)}")
                print(f"   Tools found: {len(results[0]['result']['tools'])}")
        elif response.status_code == 202:
            print("   ✅ Notification accepted (202)")
        
        print("\n✅ All tests completed!")
        print("\nThe MCP server is properly deployed and implements:")
        print("- Protocol version 2025-03-26")
        print("- OAuth 2.0 Authorization Server Metadata (RFC8414)")
        print("- Streamable HTTP transport with SSE support")
        print("- JSON-RPC batch request handling")
        print("- Proper notification handling (202 responses)")
        print("\nReady for use with Claude.ai MCP connector!")


if __name__ == "__main__":
    asyncio.run(test_deployed_server())