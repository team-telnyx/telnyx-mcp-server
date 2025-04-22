"""Telnyx messaging service."""

from typing import Any, Dict, List, Optional

from ...utils.logger import get_logger
from ..client import TelnyxClient

logger = get_logger(__name__)


class MessagingService:
    """Telnyx messaging service."""

    def __init__(self, client: Optional[TelnyxClient] = None):
        """Initialize the service.

        Args:
            client: Telnyx API client (creates a new one if not provided)
        """
        self.client = client or TelnyxClient()

    def send_message(
        self,
        from_: str,
        to: str,
        text: str,
        messaging_profile_id: Optional[str] = None,
        subject: Optional[str] = None,
        media_urls: Optional[List[str]] = None,
        webhook_url: Optional[str] = None,
        webhook_failover_url: Optional[str] = None,
        use_profile_webhooks: bool = True,
        type: Optional[str] = None,
        auto_detect: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Send a message.

        Args:
            from_: Sending address (phone number, alphanumeric sender ID, or short code)
            to: Receiving address(es)
            text: Message text
            messaging_profile_id: Messaging profile ID
            subject: Message subject
            media_urls: Media URLs
            webhook_url: Webhook URL
            webhook_failover_url: Webhook failover URL
            use_profile_webhooks: Whether to use profile webhooks
            type: The protocol for sending the message, either SMS or MMS
            auto_detect: Automatically detect if an SMS message is unusually long

        Returns:
            Dict[str, Any]: Response data
        """
        data = {
            "from": from_,
            "to": to if isinstance(to, list) else [to],
            "text": text,
            "use_profile_webhooks": use_profile_webhooks,
        }

        if messaging_profile_id:
            data["messaging_profile_id"] = messaging_profile_id

        if subject:
            data["subject"] = subject

        if media_urls:
            data["media_urls"] = media_urls

        if webhook_url:
            data["webhook_url"] = webhook_url

        if webhook_failover_url:
            data["webhook_failover_url"] = webhook_failover_url

        if type:
            data["type"] = type

        if auto_detect is not None:
            data["auto_detect"] = auto_detect

        return self.client.post("messages", data=data)

    def get_message(self, message_id: str) -> Dict[str, Any]:
        """Retrieve a message by ID.

        Args:
            message_id: The ID of the message to retrieve

        Returns:
            Dict[str, Any]: Response data containing message details
        """
        return self.client.get(f"messages/{message_id}")
