#!/usr/bin/env python3
"""Test script to verify MCP protocol implementation."""

import asyncio
import httpx
import json
import sys
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8000"
# BASE_URL = "https://app-web-3ky2b33hy2dpm.azurewebsites.net"


async def test_oauth_metadata_discovery():
    """Test OAuth 2.0 Authorization Server Metadata discovery."""
    print("\n=== Testing OAuth Metadata Discovery ===")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/.well-known/oauth-authorization-server")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                metadata = response.json()
                print("Metadata discovered successfully!")
                print(f"Authorization endpoint: {metadata.get('authorization_endpoint')}")
                print(f"Token endpoint: {metadata.get('token_endpoint')}")
                print(f"Registration endpoint: {metadata.get('registration_endpoint')}")
                return True
            else:
                print(f"Failed to discover metadata: {response.text}")
                return False
                
        except Exception as e:
            print(f"Error: {e}")
            return False


async def test_dynamic_registration():
    """Test OAuth 2.0 Dynamic Client Registration."""
    print("\n=== Testing Dynamic Client Registration ===")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/register",
                json={
                    "redirect_uris": ["http://localhost:3000/callback"],
                    "client_name": "Test MCP Client"
                }
            )
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                client_info = response.json()
                print("Client registered successfully!")
                print(f"Client ID: {client_info.get('client_id')}")
                print(f"Token endpoint auth method: {client_info.get('token_endpoint_auth_method')}")
                return client_info.get('client_id')
            else:
                print(f"Registration failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None


async def test_mcp_initialize(token: Optional[str] = None):
    """Test MCP initialization."""
    print("\n=== Testing MCP Initialize ===")
    
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
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
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/mcp",
                json=message,
                headers=headers
            )
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("Initialize successful!")
                print(f"Protocol version: {result['result']['protocolVersion']}")
                print(f"Server capabilities: {json.dumps(result['result']['capabilities'], indent=2)}")
                return True
            else:
                print(f"Initialize failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"Error: {e}")
            return False


async def test_mcp_initialized_notification(token: Optional[str] = None):
    """Test sending initialized notification."""
    print("\n=== Testing Initialized Notification ===")
    
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    message = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/mcp",
                json=message,
                headers=headers
            )
            print(f"Status: {response.status_code}")
            
            if response.status_code == 202:
                print("Notification accepted!")
                return True
            else:
                print(f"Notification failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"Error: {e}")
            return False


async def test_mcp_tools_list(token: Optional[str] = None):
    """Test listing available tools."""
    print("\n=== Testing Tools List ===")
    
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    message = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/mcp",
                json=message,
                headers=headers
            )
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                tools = result['result']['tools']
                print(f"Found {len(tools)} tools!")
                if tools:
                    print("Sample tools:")
                    for tool in tools[:5]:
                        print(f"  - {tool['name']}: {tool['description'][:60]}...")
                return len(tools) > 0
            else:
                print(f"Tools list failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"Error: {e}")
            return False


async def test_mcp_batch_request(token: Optional[str] = None):
    """Test batch JSON-RPC request."""
    print("\n=== Testing Batch Request ===")
    
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    batch = [
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/list",
            "params": {}
        },
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "resources/list",
            "params": {}
        }
    ]
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/mcp",
                json=batch,
                headers=headers
            )
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                results = response.json()
                print(f"Received {len(results)} responses")
                for result in results:
                    method = "tools" if result['id'] == 3 else "resources"
                    print(f"  - {method}: {len(result['result'].get(method, []))} items")
                return True
            else:
                print(f"Batch request failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"Error: {e}")
            return False


async def test_mcp_sse_support(token: Optional[str] = None):
    """Test SSE support."""
    print("\n=== Testing SSE Support ===")
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    message = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/list",
        "params": {}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/mcp",
                json=message,
                headers=headers
            )
            print(f"Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type')}")
            
            if "text/event-stream" in response.headers.get('content-type', ''):
                print("SSE stream received!")
                # Read first few lines
                lines = response.text.split('\n')[:5]
                for line in lines:
                    if line:
                        print(f"  {line}")
                return True
            else:
                print("No SSE stream returned")
                return False
                
        except Exception as e:
            print(f"Error: {e}")
            return False


async def main():
    """Run all tests."""
    print(f"Testing MCP server at {BASE_URL}")
    
    # Check if we need a token
    token = None
    if len(sys.argv) > 1:
        token = sys.argv[1]
        print(f"Using provided token: {token[:20]}...")
    
    # Run tests
    tests_passed = 0
    total_tests = 0
    
    # Test OAuth discovery
    total_tests += 1
    if await test_oauth_metadata_discovery():
        tests_passed += 1
    
    # Test client registration
    total_tests += 1
    client_id = await test_dynamic_registration()
    if client_id:
        tests_passed += 1
    
    # Test MCP protocol
    total_tests += 1
    if await test_mcp_initialize(token):
        tests_passed += 1
        
        # Test initialized notification
        total_tests += 1
        if await test_mcp_initialized_notification(token):
            tests_passed += 1
        
        # Test tools list
        total_tests += 1
        if await test_mcp_tools_list(token):
            tests_passed += 1
        
        # Test batch requests
        total_tests += 1
        if await test_mcp_batch_request(token):
            tests_passed += 1
        
        # Test SSE support
        total_tests += 1
        if await test_mcp_sse_support(token):
            tests_passed += 1
    
    # Summary
    print(f"\n=== Test Summary ===")
    print(f"Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))