"""Main entry point for the Telnyx MCP server."""

import logging
import os
import sys

# Set up logging before importing anything else
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("telnyx-mcp")

# Check for API key
if not os.getenv("TELNYX_API_KEY"):
    logger.error("TELNYX_API_KEY environment variable not set")
    print("Error: TELNYX_API_KEY environment variable must be set")
    sys.exit(1)

# Import server only after checking for API key
from .server import run_server

if __name__ == "__main__":
    run_server()
