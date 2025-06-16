#!/usr/bin/env python3
"""Test what Claude.ai MCP connector is actually doing"""

import httpx
import json
import asyncio
import os
from httpx_sse import aconnect_sse

async def test_claude_mcp():
    """Test MCP connection like Claude does"""
    
    # Get test token
    token = os.getenv("TEST_JWT_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjZjQ0OGQ1ZS04MDMzLTRkZjctOTJkMC0xNGJmMjI5ZGU5YjciLCJlbWFpbCI6InRlc3RAYXp1cmUuY29tIiwibmFtZSI6IlRlc3QgVXNlciIsImV4cCI6MTczNDMzNjAzNiwiaWF0IjoxNzM0MjQ5NjM2fQ.p7cDXGVxhXchJxP_U_YlJqhQMuBLi6K2IaU7x3Ywbvc")
    base_url = "https://app-web-3ky2b33hy2dpm.azurewebsites.net"
    
    print(f"Testing MCP connection to {base_url}")
    print(f"Using token: {token[:20]}...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream,application/json",
        "User-Agent": "Claude-MCP-Client/1.0"
    }
    
    # Test 1: Initialize with SSE
    print("\n1. Testing initialize with SSE (Accept: text/event-stream)...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            sse_headers = headers.copy()
            sse_headers["Accept"] = "text/event-stream"
            
            response = await client.post(
                f"{base_url}/mcp",
                headers=sse_headers,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "claude-test",
                            "version": "1.0.0"
                        }
                    }
                }
            )
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                if "text/event-stream" in response.headers.get("content-type", ""):
                    print("Got SSE response, reading events...")
                    content = response.text
                    print(f"SSE content: {content[:500]}...")
                else:
                    print(f"Got JSON response: {response.text}")
            else:
                print(f"Error response: {response.text}")
                
        except Exception as e:
            print(f"Error: {e}")
    
    # Test 2: Try SSE streaming with httpx-sse
    print("\n2. Testing SSE streaming with httpx-sse...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            sse_headers = headers.copy()
            sse_headers["Accept"] = "text/event-stream"
            
            async with aconnect_sse(
                client,
                "POST",
                f"{base_url}/mcp",
                headers=sse_headers,
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }
            ) as event_source:
                print(f"SSE connection status: {event_source.response.status_code}")
                
                # Read events
                async for sse in event_source.aiter_sse():
                    print(f"SSE Event: {sse.event}")
                    print(f"SSE Data: {sse.data[:200]}...")
                    if sse.event == "message":
                        # Parse the JSON-RPC response
                        data = json.loads(sse.data)
                        print(f"Parsed response: {json.dumps(data, indent=2)[:500]}...")
                        break
                        
        except Exception as e:
            print(f"SSE Error: {e}")
    
    # Test 3: Test /mcp/stream endpoint
    print("\n3. Testing /mcp/stream endpoint...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{base_url}/mcp/stream",
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "claude-test",
                            "version": "1.0.0"
                        }
                    }
                }
            )
            print(f"Response status: {response.status_code}")
            if response.status_code == 200:
                print(f"Response content: {response.text[:500]}...")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_claude_mcp())