"""Telnyx embeddings service."""

from typing import Any, Dict, Optional

from ...utils.logger import get_logger
from ..client import TelnyxClient

logger = get_logger(__name__)


class EmbeddingsService:
    """Telnyx embeddings service."""

    def __init__(self, client: Optional[TelnyxClient] = None):
        """Initialize the service.

        Args:
            client: Telnyx API client (creates a new one if not provided)
        """
        self.client = client or TelnyxClient()

    def list_embedded_buckets(
        self,
    ) -> Dict[str, Any]:
        """List embedded buckets.

        Returns:
            Dict[str, Any]: Response data
        """
        return self.client.get("ai/embeddings/buckets")

    def embed_url(
        self,
        request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Embed a URL.
        Args:
            request: request containing the url to embed `{url: str}`


        Returns:
            Dict[str, Any]: Response data
        """
        return self.client.post("ai/embeddings/url", data=request)

    def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings for a list of texts.

            Returns:
        Dict[str, Any]: Response data
        """
        return self.client.post("ai/embeddings", data=request)
