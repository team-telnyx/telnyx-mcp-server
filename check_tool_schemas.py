#!/usr/bin/env python3
"""Check tool schemas to understand the formatting issue."""

import asyncio
import sys
sys.path.insert(0, 'src')

from telnyx_mcp_server.mcp import mcp


async def main():
    """Check tool schemas."""
    # Import tools to register them
    from telnyx_mcp_server.tools import messaging
    
    # Get tools
    tools = await mcp.list_tools()
    
    print(f"Found {len(tools)} tools\n")
    
    # Check a few tools
    for tool in tools[:3]:
        print(f"Tool: {tool.name}")
        print(f"Description: {tool.description[:100]}...")
        print(f"Input Schema: {tool.inputSchema}")
        print("-" * 80)


if __name__ == "__main__":
    asyncio.run(main())