"""Connection related MCP tools."""

from typing import Any, Dict

from ..mcp import mcp
from ..telnyx.services.connections import ConnectionsService
from ..utils.error_handler import handle_telnyx_error
from ..utils.logger import get_logger
from ..utils.service import get_authenticated_service

logger = get_logger(__name__)


@mcp.tool()
async def list_connections(request: Dict[str, Any]) -> Dict[str, Any]:
    """List connections.

    Args:
        page: Optional integer. Page number. Defaults to 1.
        page_size: Optional integer. Page size. Defaults to 20.
        filter_connection_name_contains: Optional. Filter by connection name.
        filter_outbound_voice_profile_id: Optional. Filter by outbound voice profile ID.
        sort: Optional. Sort order (created_at, connection_name, active).

    Returns:
        Dict[str, Any]: Response data
    """
    try:
        service = get_authenticated_service(ConnectionsService)
        return service.list_connections(request)
    except Exception as e:
        logger.error(f"Error listing connections: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def get_connection(id: str) -> Dict[str, Any]:
    """Get a connection by ID.

    Args:
        id: Required. Connection ID.

    Returns:
        Dict[str, Any]: Response data
    """
    try:
        service = get_authenticated_service(ConnectionsService)
        return service.get_connection(connection_id=id)
    except Exception as e:
        logger.error(f"Error getting connection: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def update_connection(id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update a connection.

    Note:
        The Telnyx API does not support updating connections directly.
        Only GET, HEAD, and OPTIONS methods are allowed.
        Please create a new connection with the desired settings instead.

    Args:
        id: Required. Connection ID.
        data: Required. Update data.

    Returns:
        Dict[str, Any]: Response data

    Raises:
        Exception: The Telnyx API does not support updating connections directly.
    """
    try:
        service = get_authenticated_service(ConnectionsService)
        return service.update_connection(connection_id=id, data=data)
    except Exception as e:
        logger.error(f"Error updating connection: {e}")
        raise handle_telnyx_error(e)
