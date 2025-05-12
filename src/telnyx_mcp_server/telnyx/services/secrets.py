"""Telnyx secrets manager service."""

from typing import Any, Dict, Optional

from ...utils.logger import get_logger
from ..client import TelnyxClient

logger = get_logger(__name__)


class SecretsService:
    """Telnyx secrets manager service."""

    def __init__(self, client: Optional[TelnyxClient] = None):
        """Initialize the service.

        Args:
            client: Telnyx API client (creates a new one if not provided)
        """
        self.client = client or TelnyxClient()

    def list_integration_secrets(
        self,
        page: int = 1,
        page_size: int = 25,
        filter_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List integration secrets.

        Args:
            page: Page number
            page_size: Page size
            filter_type: Filter by secret type (bearer, basic)

        Returns:
            Dict[str, Any]: Response data
        """
        params = {
            "page[number]": page,
            "page[size]": page_size,
        }

        if filter_type:
            params["filter[type]"] = filter_type

        return self.client.get("integration_secrets", params=params)

    def create_integration_secret(
        self, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create an integration secret.

        Args:
            identifier: The unique identifier of the secret
            type: The type of secret (bearer, basic)
            token: The token for the secret (required for bearer type)
            username: The username for the secret (required for basic type)
            password: The password for the secret (required for basic type)

        Returns:
            Dict[str, Any]: Response data
        """
        return self.client.post("integration_secrets", data=request)

    def delete_integration_secret(self, id: str) -> Dict[str, Any]:
        """Delete an integration secret.

        Args:
            id: Secret ID

        Returns:
            Dict[str, Any]: Response data (empty dict on success)
        """
        return self.client.delete(f"integration_secrets/{id}")
