"""Telnyx connections service."""

from typing import Any, Dict, Optional

from ...utils.logger import get_logger
from ..client import TelnyxClient

logger = get_logger(__name__)


class ConnectionsService:
    """Service for managing Telnyx connections."""

    def __init__(self, client: Optional[TelnyxClient] = None):
        """Initialize the service with a Telnyx client."""
        self.client = client or TelnyxClient()

    def list_connections(
        self,
        request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """List connections.

        Args:
            request: Request parameters for listing connections

        Returns:
            Dict[str, Any]: Response data
        """
        params = {
            "page[number]": request.get("page", 1),
            "page[size]": request.get("page_size", 20),
        }

        if request.get("filter_connection_name_contains"):
            params["filter[connection_name_contains]"] = (
                request["filter_connection_name_contains"]
            )

        if request.get("filter_outbound_voice_profile_id"):
            params["filter[outbound_voice_profile_id]"] = (
                request["filter_outbound_voice_profile_id"]
            )

        if request.get("sort"):
            params["sort"] = request["sort"]

        response = self.client.get("connections", params=params)
        if isinstance(response, dict):
            return response
        return response.json()

    def get_connection(self, connection_id: str) -> Dict[str, Any]:
        """Get a connection by ID.

        Args:
            connection_id: Connection ID

        Returns:
            Dict[str, Any]: Response data
        """
        response = self.client.get(f"connections/{connection_id}")
        if isinstance(response, dict):
            return response
        return response.json()

    def update_connection(
        self,
        connection_id: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a connection.

        Note:
            The Telnyx API does not support updating connections directly.
            Only GET, HEAD, and OPTIONS methods are allowed.
            Please create a new connection with the desired settings instead.

        Args:
            connection_id: Connection ID
            data: Update data

        Returns:
            Dict[str, Any]: Response data

        Raises:
            Exception: The Telnyx API does not support updating connections directly.
        """
        raise Exception(
            "The Telnyx API does not support updating connections directly. "
            "Please create a new connection with the desired settings instead."
        )
