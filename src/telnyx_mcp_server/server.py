"""Telnyx MCP server using STDIO transport."""

import argparse
import atexit
import os
import signal
import sys
import threading
import time
from typing import List, Optional

from dotenv import load_dotenv

from .config import settings
from .mcp import mcp  # Import the shared MCP instance
from .telnyx.client import TelnyxClient
from .telnyx.services.assistants import AssistantsService
from .telnyx.services.connections import ConnectionsService
from .telnyx.services.messaging import MessagingService
from .telnyx.services.numbers import NumbersService
from .tools import *  # Import all tools
from .utils.logger import get_logger
from .webhook import (
    start_webhook_handler,
    stop_webhook_handler,
)

def parse_args(args=None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Telnyx MCP Server")

    # Webhook arguments
    parser.add_argument(
        "--webhook-enabled",
        action="store_true",
        default=settings.webhook_enabled,
        help="Enable webhook receiver",
    )
    parser.add_argument(
        "--ngrok-enabled",
        action="store_true",
        default=settings.ngrok_enabled,
        help="Enable ngrok tunnel for webhooks",
    )
    parser.add_argument(
        "--ngrok-authtoken",
        type=str,
        default=settings.ngrok_authtoken,
        help="Ngrok authentication token",
    )
    parser.add_argument(
        "--ngrok-url",
        type=str,
        default=settings.ngrok_url,
        help="Predefined ngrok URL to use instead of creating a new tunnel",
    )
    parser.add_argument(
        "--tools",
        help="Comma-separated list of tool names to enable. If not specified, all tools are enabled.",
        type=str,
    )
    parser.add_argument(
        "--exclude-tools",
        help="Comma-separated list of tool names to disable.",
        type=str,
    )
    parser.add_argument(
        "--list-tools",
        help="List all available tools and exit.",
        action="store_true",
    )

    # Ignore unknown arguments to prevent errors with additional CLI parameters
    # This allows the server to be started with additional CLI args that may be
    # used by other implementers without causing errors
    return parser.parse_known_args(args)[0]


# Check if just listing tools first
try:
    args = parse_args()
    just_listing = args.list_tools
except:
    just_listing = False

logger = get_logger(__name__)

# Load environment variables
load_dotenv()

# Initialize Telnyx client with API key from environment
api_key = os.getenv("TELNYX_API_KEY", "")
if not api_key:
    logger.critical("TELNYX_API_KEY environment variable must be set")
    sys.exit(1)
if not just_listing:
    api_key = os.getenv("TELNYX_API_KEY", "")
    if not api_key:
        logger.error("TELNYX_API_KEY environment variable must be set")
        print("Error: TELNYX_API_KEY environment variable must be set")
        sys.exit(1)
else:
    # Use a dummy key for listing tools (won't be used for API calls)
    api_key = "dummy_key_for_listing_tools"

# Import MCP and setup services
from .mcp import mcp  # Import the shared MCP instance
from .telnyx.client import TelnyxClient
from .telnyx.services.assistants import AssistantsService
from .telnyx.services.connections import ConnectionsService
from .telnyx.services.embeddings import EmbeddingsService
from .telnyx.services.messaging import MessagingService
from .telnyx.services.numbers import NumbersService
from .telnyx.services.secrets import SecretsService
from .tools import *  # Import all tools

telnyx_client = TelnyxClient(api_key=api_key)
numbers_service = NumbersService(telnyx_client)
connections_service = ConnectionsService(telnyx_client)
messaging_service = MessagingService(telnyx_client)
assistants_service = AssistantsService(telnyx_client)
embeddings_service = EmbeddingsService(telnyx_client)
secrets_service = SecretsService(telnyx_client)


def get_enabled_tools() -> Optional[List[str]]:
    """
    Get list of enabled tools from CLI args or environment variable.

    Returns:
        Optional[List[str]]: List of tool names to enable, or None to enable all tools
    """
    try:
        args = parse_args()

        # CLI args take precedence over environment variables
        if args.tools:
            logger.info(f"Using tool list from CLI arguments: {args.tools}")
            return [tool.strip() for tool in args.tools.split(",")]
    except:
        # If argument parsing fails, fall back to environment variables
        pass

    # Check for environment variable
    env_tools = os.getenv("TELNYX_MCP_TOOLS")
    if env_tools:
        logger.info(f"Using tool list from environment variable: {env_tools}")
        return [tool.strip() for tool in env_tools.split(",")]

    return None


def get_excluded_tools() -> List[str]:
    """
    Get list of tools to exclude from CLI args or environment variable.

    Returns:
        List[str]: List of tool names to disable
    """
    try:
        args = parse_args()

        # CLI args take precedence over environment variables
        if args.exclude_tools:
            logger.info(
                f"Using tool exclusion list from CLI arguments: {args.exclude_tools}"
            )
            return [tool.strip() for tool in args.exclude_tools.split(",")]
    except:
        # If argument parsing fails, fall back to environment variables
        pass

    # Check for environment variable
    env_exclude_tools = os.getenv("TELNYX_MCP_EXCLUDE_TOOLS")
    if env_exclude_tools:
        logger.info(
            f"Using tool exclusion list from environment variable: {env_exclude_tools}"
        )
        return [tool.strip() for tool in env_exclude_tools.split(",")]

    return []


async def list_all_tools() -> None:
    """List all available tools and exit."""

    # Create an instance of the MCP server to list the tools
    tools_dict = await mcp.get_tools()

    # Sort and print the tools
    tools = sorted(tools_dict.items(), key=lambda x: x[0])

    print("\nAvailable MCP Tools:")
    print("===================")
    for name, tool in tools:
        description = (
            tool.description if tool.description else "No description"
        )
        print(f"- {name}: {description}")
    print(
        "\nUse --tools to specify a comma-separated list of tools to enable."
    )
    print(
        "Use --exclude-tools to specify a comma-separated list of tools to disable."
    )
    print(f"\nTotal tools: {len(tools)}")


def setup_webhook_server(args: argparse.Namespace) -> None:
    """
    Set up the webhook handler based on command line arguments.

    Args:
        args: Command line arguments
    """
    # Update settings from command line arguments
    settings.webhook_enabled = args.webhook_enabled
    settings.ngrok_enabled = args.ngrok_enabled

    if args.ngrok_authtoken:
        settings.ngrok_authtoken = args.ngrok_authtoken

    # CRITICAL: Ignore any ngrok_url setting to prevent TLS errors
    # This effectively makes custom domains impossible to set
    if hasattr(settings, "ngrok_url"):
        # Always force to None regardless of command line args or env vars
        try:
            object.__setattr__(settings, "ngrok_url", None)
            logger.info(
                "Forced ngrok_url to None (custom domains cause TLS errors)"
            )
        except Exception as attr_err:
            logger.warning(
                f"Could not override ngrok_url attribute: {attr_err}"
            )

    # Log settings
    logger.info(f"Webhook enabled: {settings.webhook_enabled}")
    logger.info(f"Ngrok enabled: {settings.ngrok_enabled}")

    if settings.ngrok_enabled:
        logger.info(
            f"Ngrok auth token provided: {bool(settings.ngrok_authtoken)}"
        )
        logger.info(f"Ngrok URL provided: {bool(settings.ngrok_url)}")
        # Dump the source of the setting to see where it's coming from
        logger.info(f"Ngrok URL setting type: {type(settings.ngrok_url)}")
        logger.info(f"Ngrok URL setting value: {settings.ngrok_url!r}")
        logger.info(
            f"Raw environment value: {os.getenv('NGROK_URL', 'NOT_SET')!r}"
        )

        if settings.ngrok_url:
            logger.info(f"Using Ngrok URL: {settings.ngrok_url}")

    # Start webhook handler if enabled
    if settings.webhook_enabled:
        logger.info("Starting webhook handler...")

        # Only clean up our resources using the SDK, don't kill processes
        try:
            import ngrok

            try:
                logger.info("Cleaning up existing ngrok SDK resources...")
                ngrok.disconnect()
                time.sleep(1)  # Brief pause to allow cleanup
            except Exception as cleanup_err:
                logger.warning(
                    f"NGrok cleanup warning (non-fatal): {cleanup_err}"
                )

            # Force disable any custom domain in NGrok config
            if settings.ngrok_enabled and hasattr(ngrok, "set_config"):
                try:
                    ngrok.set_config(domain=None)
                    logger.info(
                        "Explicitly disabled custom domain in NGrok configuration"
                    )
                except Exception as config_err:
                    logger.warning(
                        f"Could not override NGrok domain config: {config_err}"
                    )

            # Check for existing sessions and warn (but don't kill them)
            if os.name == "posix" and hasattr(ngrok, "list_tunnels"):
                try:
                    tunnels = ngrok.list_tunnels()
                    if tunnels:
                        logger.warning(
                            f"Found {len(tunnels)} existing NGrok tunnels"
                        )
                        logger.warning(
                            "This may cause session limit errors if you've reached your account limit"
                        )
                except Exception:
                    pass
        except ImportError:
            logger.warning("NGrok module not available for pre-cleanup")

        # Start the webhook handler
        webhook_url = start_webhook_handler()

        if webhook_url:
            logger.info(f"Webhook public URL: {webhook_url}")
            logger.info(
                f"Webhook endpoint URL: {webhook_url}{settings.webhook_path}"
            )
            logger.info(
                f"Webhook information available through resource://webhook/info"
            )
        else:
            # This is a fatal error - webhooks are required
            logger.critical("FATAL ERROR: Failed to start webhook handler")
            logger.critical("Webhooks are required for MCP server operation")
            logger.critical("The most likely causes are:")
            logger.critical("1. NGrok session limit reached - check dashboard")
            logger.critical("2. Custom domain TLS certificate issues")
            logger.critical("3. Network connectivity problems")
            logger.critical(
                "The server will exit. Please resolve these issues before restarting."
            )
            sys.exit(1)  # Exit with error code - fail decisively

    # Register cleanup handlers
    atexit.register(cleanup_webhook_server)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Add SIGHUP handler for Unix-like systems
    if os.name == "posix":
        signal.signal(signal.SIGHUP, signal_handler)


# Global variables
parent_watcher_thread: Optional[threading.Thread] = None
parent_pid: int = os.getppid()


def watch_parent_process() -> None:
    """
    Watch the parent process and exit if it's gone.

    This function runs in a background thread and periodically checks if the
    parent process (Claude Desktop) is still running. If the parent process
    is gone, it cleans up resources and exits.
    """
    global parent_watcher_thread

    def _watch_loop():
        """Inner function to watch the parent process in a loop."""
        consecutive_errors = 0
        max_consecutive_errors = 3

        # Default check interval is 5 seconds
        check_interval = 5

        while True:
            try:
                parent_running = False

                # Use different methods based on platform
                if os.name == "posix":
                    try:
                        # Check if parent process still exists by sending signal 0
                        # This doesn't actually send a signal, just checks if the process exists
                        os.kill(parent_pid, 0)
                        parent_running = True
                    except OSError:
                        # The parent process is gone
                        parent_running = False
                else:
                    # On Windows, check if we can get process info
                    try:
                        # Import only when needed to avoid unnecessary dependency
                        import ctypes

                        kernel32 = ctypes.windll.kernel32
                        handle = kernel32.OpenProcess(1, False, parent_pid)
                        if handle != 0:
                            # Process exists, close the handle
                            kernel32.CloseHandle(handle)
                            parent_running = True
                        else:
                            # Process doesn't exist
                            parent_running = False
                    except Exception as e:
                        logger.debug(
                            f"Error checking Windows parent process: {e}"
                        )
                        # On error, assume parent is still running
                        parent_running = True

                # If parent is not running, clean up and exit
                if not parent_running:
                    logger.warning(
                        "Parent process (Claude Desktop) is gone, shutting down..."
                    )
                    cleanup_webhook_server()
                    logger.info("Exiting MCP server cleanly")
                    os._exit(0)  # Force exit without running finalizers

                # Reset error counter on successful check
                consecutive_errors = 0

                # Sleep for the check interval
                time.sleep(check_interval)

            except Exception as e:
                # Count consecutive errors
                consecutive_errors += 1
                logger.error(f"Error in parent process watcher: {e}")

                if consecutive_errors >= max_consecutive_errors:
                    logger.critical(
                        f"Too many consecutive errors ({consecutive_errors}) "
                        "in parent process watcher. Continuing but may not "
                        "detect parent process termination properly."
                    )

                # Increase sleep time on error to prevent tight loops
                error_sleep = min(check_interval * consecutive_errors, 30)
                time.sleep(error_sleep)

    # Create and start the watcher thread
    parent_watcher_thread = threading.Thread(
        target=_watch_loop, daemon=True, name="ParentProcessWatcher"
    )
    parent_watcher_thread.start()
    logger.info(f"Started watching parent process (PID: {parent_pid})")


def cleanup_webhook_server() -> None:
    """Clean up webhook handler resources."""
    if settings.webhook_enabled:
        stop_webhook_handler()


def signal_handler(sig, frame) -> None:
    """Handle termination signals."""
    logger.info(f"Received signal {sig}, shutting down...")
    cleanup_webhook_server()
    sys.exit(0)


def run_server() -> None:
    """Run the server using STDIO transport."""
    try:
        # Check if just listing tools
        args = parse_args()
        if args.list_tools:
            import asyncio

            asyncio.run(list_all_tools())
            return
    except:
        # If argument parsing fails, proceed with normal server startup
        pass

    # Parse command line arguments
    args = parse_args()

    logger.info("Starting Telnyx MCP server with STDIO transport")
    logger.info("Using API key from environment variables")

    # Get tool filtering settings
    enabled_tools = get_enabled_tools()
    excluded_tools = get_excluded_tools()

    # Configure tool filtering in MCP instance
    if enabled_tools is not None:
        logger.info(f"Enabling specific tools: {', '.join(enabled_tools)}")
        mcp.set_enabled_tools(enabled_tools)

    if excluded_tools:
        logger.info(f"Excluding tools: {', '.join(excluded_tools)}")
        mcp.set_excluded_tools(excluded_tools)

    # Start the parent process watcher
    watch_parent_process()

    # Set up webhook server if enabled
    setup_webhook_server(args)

    # Use FastMCP's run method to start the server
    mcp.run()


# This function is used when running the server with uvx
def main() -> None:
    """Entry point for running the server with uvx."""
    run_server()


# This allows the script to be run directly
if __name__ == "__main__":
    main()
