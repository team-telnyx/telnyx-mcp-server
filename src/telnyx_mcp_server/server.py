"""Telnyx MCP server using STDIO transport."""

import os
import sys

from dotenv import load_dotenv

from .mcp import mcp  # Import the shared MCP instance
from .telnyx.client import TelnyxClient
from .telnyx.services.assistants import AssistantsService
from .telnyx.services.connections import ConnectionsService
from .telnyx.services.messaging import MessagingService
from .telnyx.services.numbers import NumbersService
from .tools import *  # Import all tools
from .utils.logger import get_logger

logger = get_logger(__name__)

# Load environment variables
load_dotenv()

# Initialize Telnyx client with API key from environment
api_key = os.getenv("TELNYX_API_KEY", "")
if not api_key:
    logger.error("TELNYX_API_KEY environment variable must be set")
    print("Error: TELNYX_API_KEY environment variable must be set")
    sys.exit(1)

telnyx_client = TelnyxClient(api_key=api_key)
numbers_service = NumbersService(telnyx_client)
connections_service = ConnectionsService(telnyx_client)
messaging_service = MessagingService(telnyx_client)
assistants_service = AssistantsService(telnyx_client)


def run_server() -> None:
    """Run the server using STDIO transport."""
    logger.info("Starting Telnyx MCP server with STDIO transport")
    logger.info("Using API key from environment variables")

    # Use FastMCP's run method to start the server
    mcp.run()


# This function is used when running the server with uvx
def main() -> None:
    """Entry point for running the server with uvx."""
    run_server()


# This allows the script to be run directly
if __name__ == "__main__":
    main()