"""Webhook management and information tools."""

from typing import Any, Dict

from pydantic.networks import AnyUrl

from ..config import settings
from ..mcp import mcp
from ..utils.logger import get_logger
from ..webhook import get_webhook_history, webhook_handler

logger = get_logger(__name__)

# Resource URI for webhook info
WEBHOOK_INFO_URI = "resource://webhook/info"


@mcp.resource(WEBHOOK_INFO_URI)
def get_webhook_info() -> Dict[str, Any]:
    """
    Get information about the webhook tunnel.

    Returns:
        Dict[str, Any]: Webhook tunnel information
    """
    # Get last error from webhook history if available
    last_error = None
    try:
        for event in get_webhook_history(5):
            if event.get("event_type") == "ngrok.error":
                last_error = event.get("payload", {}).get(
                    "error", "Unknown error"
                )
                break
    except Exception:
        pass

    return {
        "webhook_tunnel": {
            "enabled": settings.webhook_enabled,
            "public_url": webhook_handler.public_url,
            "active": webhook_handler.listener is not None,
            "path": settings.webhook_path,
            "full_url": f"{webhook_handler.public_url}{settings.webhook_path}"
            if webhook_handler.public_url
            else None,
            "last_error": last_error,
            "status": "active"
            if webhook_handler.listener is not None
            else "inactive",
        },
        "ngrok": {
            "enabled": settings.ngrok_enabled,
            "auth_token_provided": bool(settings.ngrok_authtoken),
            "custom_domain_setting": bool(settings.ngrok_url),
            "using_dynamic_url": webhook_handler.public_url is not None
            and (
                settings.ngrok_url is None
                or settings.ngrok_url not in webhook_handler.public_url
            ),
        },
    }


async def notify_webhook_info_updated(session):
    """Notify clients that the webhook info resource has been updated."""
    try:
        await session.send_resource_updated(AnyUrl(WEBHOOK_INFO_URI))
        logger.info(
            f"Sent resource update notification for {WEBHOOK_INFO_URI}"
        )
    except Exception as e:
        logger.error(f"Failed to send resource update notification: {str(e)}")


@mcp.tool()
async def get_webhook_events(
    limit: int = 10, event_type: str = None
) -> Dict[str, Any]:
    """
    Get the most recent webhook events received by the handler.

    Args:
        limit: Maximum number of events to return (default: 10)
        event_type: Filter events by type (default: all types)

    Returns:
        Dict containing webhook events and metadata
    """
    # Get webhook history
    history = get_webhook_history()

    # Apply event_type filter if specified
    if event_type:
        history = [h for h in history if h.get("event_type") == event_type]

    # Apply limit
    if limit > 0:
        history = history[:limit]

    webhook_status = {
        "count": len(history),
        "tunnel_enabled": settings.webhook_enabled,
        "has_webhooks": len(history) > 0,
        "webhook_url": webhook_handler.public_url,
        "webhook_endpoint": f"{webhook_handler.public_url}{settings.webhook_path}"
        if webhook_handler.public_url
        else None,
    }

    return {"events": history, "status": webhook_status}
