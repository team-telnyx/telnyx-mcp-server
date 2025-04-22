"""Phone number related MCP tools."""

from typing import Any, Dict

from pydantic import Field

from ..mcp import mcp
from ..telnyx.services.numbers import NumbersService
from ..utils.error_handler import handle_telnyx_error
from ..utils.logger import get_logger
from ..utils.service import get_authenticated_service

logger = get_logger(__name__)


@mcp.tool()
async def list_phone_numbers(request: Dict[str, Any]) -> Dict[str, Any]:
    """List phone numbers.

    Args:
        page: Optional integer. Page number. Defaults to 1.
        page_size: Optional integer. Page size. Defaults to 20.
        filter_tag: Optional. Filter by phone number tag.
        filter_phone_number: Optional. Filter by phone number.
        filter_status: Optional. Filter by phone number status.
        filter_country_iso_alpha2: Optional. Filter by country ISO alpha-2 code.

    Returns:
        Dict[str, Any]: Response data
    """
    try:
        service = get_authenticated_service(NumbersService)
        return service.list_phone_numbers(**request)
    except Exception as e:
        logger.error(f"Error listing phone numbers: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def get_phone_number(
    id: str = Field(..., description="Phone number ID as string"),
) -> Dict[str, Any]:
    """Get a phone number by ID.

    Args:
        id: Phone number ID as string

    Returns:
        Dict[str, Any]: Response data containing Number Object(s) (record_type: "phone_number")
    """
    try:
        service = get_authenticated_service(NumbersService)
        return service.get_phone_number(id=id)
    except Exception as e:
        logger.error(f"Error getting phone number: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def update_phone_number(id: str, request: Dict[str, Any]) -> Dict[str, Any]:
    """Update a phone number.

    Args:
        id: Required. Phone number ID.
        connection_id: Optional. Connection ID to associate with the number.
        tags: Optional. List of tags to associate with the number.

    Returns:
        Dict[str, Any]: Response data
    """
    try:
        service = get_authenticated_service(NumbersService)
        return service.update_phone_number(id=id, data=request)
    except Exception as e:
        logger.error(f"Error updating phone number: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def list_available_phone_numbers(request: Dict[str, Any]) -> Dict[str, Any]:
    """List available phone numbers.

    Args:
        page: Optional integer. Page number. Defaults to 1.
        page_size: Optional integer. Page size. Defaults to 20.
        filter_phone_number_starts_with: Optional. Filter numbers starting with pattern.
        filter_phone_number_ends_with: Optional. Filter numbers ending with pattern.
        filter_phone_number_contains: Optional. Filter numbers containing pattern.
        filter_locality: Optional. Filter by locality (city).
        filter_administrative_area: Optional. Filter by administrative area (state).
        filter_country_code: Optional. Filter by country code.
        filter_features: Optional. List of features to filter by.

    Returns:
        Dict[str, Any]: Response data
    """
    try:
        service = get_authenticated_service(NumbersService)
        filter_params = {
            key: value
            for key, value in request.items()
            if key.startswith("filter_")
        }
        base_params = {
            key: value
            for key, value in request.items()
            if not key.startswith("filter_")
        }
        return service.list_available_phone_numbers(
            **base_params, **filter_params
        )
    except Exception as e:
        logger.error(f"Error listing available phone numbers: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def initiate_phone_number_order(request: Dict[str, Any]) -> Dict[str, Any]:
    """Initiate a phone number order. 

    Args:
        phone_number: Required. Phone number to buy.
        connection_id: Optional. Connection ID to associate with the number.

    Returns:
        Dict[str, Any]: Response data
    """
    try:
        service = get_authenticated_service(NumbersService)
        return service.buy_phone_number(**request)
    except Exception as e:
        logger.error(f"Error buying phone number: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def update_phone_number_messaging_settings(id: str, request: Dict[str, Any]) -> Dict[str, Any]:
    """Update the messaging profile and/or messaging product of a phone number.

    Args:
        id: Required. The phone number ID to update.
        messaging_profile_id: Optional. Configure the messaging profile this phone number is assigned to. Set to null to keep the current value, set to empty string to unassign, or set to a UUID to assign to that messaging profile.
        messaging_product: Optional. Configure the messaging product for this number. Set to null to keep the current value, or set to a product ID to change.

    Returns:
        Dict[str, Any]: Response data
    """
    try:
        service = get_authenticated_service(NumbersService)
        return service.update_phone_number_messaging_settings(id=id, **request)
    except Exception as e:
        logger.error(f"Error updating phone number messaging settings: {e}")
        raise handle_telnyx_error(e)
