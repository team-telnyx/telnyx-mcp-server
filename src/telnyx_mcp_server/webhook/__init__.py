"""Webhook receiver module for Telnyx MCP server."""

from .handler import NgrokTunnelHandler
from .server import get_webhook_history

# Create a single shared instance
webhook_handler = NgrokTunnelHandler()


def start_webhook_handler() -> str:
    """Start the webhook tunnel handler and return the public URL."""
    return webhook_handler.start()


def stop_webhook_handler() -> None:
    """Stop the webhook tunnel handler."""
    webhook_handler.stop()


__all__ = [
    "start_webhook_handler",
    "stop_webhook_handler",
    "get_webhook_history",
    "webhook_handler",
]
