"""Messaging related MCP tools."""

from typing import Any, Dict

from ..mcp import mcp
from ..telnyx.services.messaging import MessagingService
from ..utils.error_handler import handle_telnyx_error
from ..utils.logger import get_logger
from ..utils.service import get_authenticated_service

logger = get_logger(__name__)


@mcp.tool()
async def send_message(request: Dict[str, Any]) -> Dict[str, Any]:
    """Send a message.

    Args:
        from_: Required. Sending address (phone number, alphanumeric sender ID, or short code).
        to: Required. Receiving address(es).
        text: Required. Message text.
        messaging_profile_id: Optional. Messaging profile ID.
        subject: Optional. Message subject.
        media_urls: Optional. List of media URLs.
        webhook_url: Optional. Webhook URL.
        webhook_failover_url: Optional. Webhook failover URL.
        use_profile_webhooks: Optional boolean. Whether to use profile webhooks. Defaults to True.
        type: Optional. The protocol for sending the message, either "SMS" or "MMS".
        auto_detect: Optional boolean. Automatically detect if an SMS message is unusually long.

    Returns:
        Dict[str, Any]: Response data
    """
    try:
        service = get_authenticated_service(MessagingService)
        return service.send_message(**request)
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def get_message(message_id: str) -> Dict[str, Any]:
    """Retrieve a message by ID.

    Args:
        message_id: The ID of the message to retrieve

    Returns:
        Dict[str, Any]: Response data containing message details
    """
    try:
        service = get_authenticated_service(MessagingService)
        return service.get_message(message_id)
    except Exception as e:
        logger.error(f"Error retrieving message: {e}")
        raise handle_telnyx_error(e)
