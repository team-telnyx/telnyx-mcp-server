"""Service utilities."""

from typing import Any, Type

from .logger import get_logger

logger = get_logger(__name__)

def get_authenticated_service(service_cls: Type[Any]) -> Any:
    """Get an authenticated service using the API key from environment.

    Args:
        service_cls: Service class to instantiate

    Returns:
        Service instance with authenticated client
    """
    logger.info(f"Getting authenticated service for {service_cls.__name__}")

    # Use the client from mcp.py that's already initialized with API key
    from ..mcp import telnyx_client

    # Log masked API key at debug level
    if hasattr(telnyx_client, "api_key") and telnyx_client.api_key:
        masked_key = (
            f"{telnyx_client.api_key[:5]}..."
            if len(telnyx_client.api_key) > 5
            else "[REDACTED]"
        )
        logger.debug(f"Using client with API key: {masked_key}")

    return service_cls(telnyx_client)