"""Secrets manager related MCP tools."""

from typing import Any, Dict

from pydantic import Field

from ..mcp import mcp
from ..telnyx.services.secrets import SecretsService
from ..utils.error_handler import handle_telnyx_error
from ..utils.logger import get_logger
from ..utils.service import get_authenticated_service

logger = get_logger(__name__)


@mcp.tool()
async def list_integration_secrets(request: Dict[str, Any]) -> Dict[str, Any]:
    """List integration secrets.

    Args:
        page: Optional integer. Page number. Defaults to 1.
        page_size: Optional integer. Page size. Defaults to 25.
        filter_type: Optional. Filter by secret type (bearer, basic).

    Returns:
        Dict[str, Any]: Response data containing Integration Secret Object(s) (record_type: "integration_secret")
    """
    try:
        service = get_authenticated_service(SecretsService)
        return service.list_integration_secrets(request)
    except Exception as e:
        logger.error(f"Error listing integration secrets: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def create_integration_secret(request: Dict[str, Any]) -> Dict[str, Any]:
    """Create an integration secret.

    Args:
        identifier: Required. The unique identifier of the secret.
        type: Required. The type of secret (bearer, basic).
        token: Optional. The token for the secret (required for bearer type).
        username: Optional. The username for the secret (required for basic type).
        password: Optional. The password for the secret (required for basic type).

    Returns:
        Dict[str, Any]: Response data containing the created Integration Secret Object (record_type: "integration_secret")
    """
    try:
        service = get_authenticated_service(SecretsService)
        return service.create_integration_secret(request)
    except Exception as e:
        logger.error(f"Error creating integration secret: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def delete_integration_secret(
    id: str = Field(..., description="Secret ID as string"),
) -> Dict[str, Any]:
    """Delete an integration secret.

    Args:
        id: Required. Secret ID.

    Returns:
        Dict[str, Any]: Empty response on success
    """
    try:
        service = get_authenticated_service(SecretsService)
        return service.delete_integration_secret(id=id)
    except Exception as e:
        logger.error(f"Error deleting integration secret: {e}")
        raise handle_telnyx_error(e)
