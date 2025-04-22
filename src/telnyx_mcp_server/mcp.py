"""Simple MCP server using FastMCP framework with STDIO transport."""

import os

from dotenv import load_dotenv
from fastmcp import FastMCP

from .telnyx.client import TelnyxClient

# Load environment variables
load_dotenv()

# Get API key from environment
api_key = os.getenv("TELNYX_API_KEY", "")
if not api_key:
    raise ValueError("TELNYX_API_KEY environment variable must be set")

# Create a single shared MCP instance
mcp = FastMCP("Telnyx MCP")

# Initialize Telnyx client with API key from environment
telnyx_client = TelnyxClient(api_key=api_key)
