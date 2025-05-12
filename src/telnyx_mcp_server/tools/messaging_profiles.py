"""Messaging profiles related MCP tools."""

from typing import Any, Dict

from ..mcp import mcp
from ..telnyx.services.messaging_profiles import MessagingProfilesService
from ..utils.error_handler import handle_telnyx_error
from ..utils.logger import get_logger
from ..utils.service import get_authenticated_service

logger = get_logger(__name__)


@mcp.tool()
async def list_messaging_profiles(request: Dict[str, Any]) -> Dict[str, Any]:
    """List messaging profiles.

    Args:
        page: Optional integer. Page number. Defaults to 1.
        page_size: Optional integer. Page size. Defaults to 20.
        filter_name: Optional. Filter by profile name.

    Returns:
        Dict[str, Any]: Response data
    """
    try:
        service = get_authenticated_service(MessagingProfilesService)
        return service.list_messaging_profiles(**request)
    except Exception as e:
        logger.error(f"Error listing messaging profiles: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def create_messaging_profile(request: Dict[str, Any]) -> Dict[str, Any]:
    """Create a messaging profile.

    Args:
        name: Required. A user friendly name for the messaging profile.
        whitelisted_destinations: Required. List of destinations to which messages are allowed to be sent (ISO 3166-1 alpha-2 country codes). Use ["*"] to allow all destinations.
        enabled: Optional boolean. Specifies whether the messaging profile is enabled. Defaults to True.
        webhook_url: Optional. The URL where webhooks related to this messaging profile will be sent.
        webhook_failover_url: Optional. The failover URL for webhooks if the primary URL fails.
        webhook_api_version: Optional. Webhook format version ("1", "2", or "2010-04-01"). Defaults to "2".
        number_pool_settings: Optional dictionary. Number pool configuration with possible settings:
            - use_pool: Boolean indicating whether to use number pool.
            - sticky_sender: Boolean indicating whether to use sticky sender.
            - pool_weights: Dictionary mapping phone number types to weights.
        url_shortener_settings: Optional dictionary. URL shortener configuration with possible settings:
            - enabled: Boolean indicating whether URL shortening is enabled.
            - domains: List of domains to be shortened.
        alpha_sender: Optional. The alphanumeric sender ID for destinations requiring it.
        daily_spend_limit: Optional. Maximum daily spend in USD before midnight UTC.
        daily_spend_limit_enabled: Optional boolean. Whether to enforce the daily spend limit.
        mms_fall_back_to_sms: Optional boolean. Enables SMS fallback for MMS messages.
        mms_transcoding: Optional boolean. Enables automated resizing of MMS media.

    Returns:
        Dict[str, Any]: Response data
    """
    try:
        service = get_authenticated_service(MessagingProfilesService)
        return service.create_messaging_profile(**request)
    except Exception as e:
        logger.error(f"Error creating messaging profile: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def get_messaging_profile(profile_id: str) -> Dict[str, Any]:
    """Retrieve a messaging profile by ID.

    Args:
        profile_id: The ID of the messaging profile to retrieve

    Returns:
        Dict[str, Any]: Response data containing messaging profile details
    """
    try:
        service = get_authenticated_service(MessagingProfilesService)
        return service.get_messaging_profile(profile_id)
    except Exception as e:
        logger.error(f"Error retrieving messaging profile: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def update_messaging_profile(
    profile_id: str, request: Dict[str, Any]
) -> Dict[str, Any]:
    """Update a messaging profile.

    Args:
        profile_id: Required. The ID of the messaging profile to update.
        name: Optional. A user friendly name for the messaging profile.
        enabled: Optional boolean. Specifies whether the messaging profile is enabled.
        webhook_url: Optional. The URL where webhooks related to this messaging profile will be sent.
        webhook_failover_url: Optional. The failover URL for webhooks if the primary URL fails.
        webhook_api_version: Optional. Webhook format version ("1", "2", or "2010-04-01").
        whitelisted_destinations: Optional list. Destinations to which messages are allowed (ISO 3166-1 alpha-2 country codes). Use ["*"] to allow all destinations.
        v1_secret: Optional. Secret used to authenticate with v1 endpoints.
        number_pool_settings: Optional dictionary. Number pool configuration with possible settings:
            - use_pool: Boolean indicating whether to use number pool.
            - sticky_sender: Boolean indicating whether to use sticky sender.
            - pool_weights: Dictionary mapping phone number types to weights.
        url_shortener_settings: Optional dictionary. URL shortener configuration with possible settings:
            - enabled: Boolean indicating whether URL shortening is enabled.
            - domains: List of domains to be shortened.
        alpha_sender: Optional. The alphanumeric sender ID for destinations requiring it.
        daily_spend_limit: Optional. Maximum daily spend in USD before midnight UTC.
        daily_spend_limit_enabled: Optional boolean. Whether to enforce the daily spend limit.
        mms_fall_back_to_sms: Optional boolean. Enables SMS fallback for MMS messages.
        mms_transcoding: Optional boolean. Enables automated resizing of MMS media.

    Returns:
        Dict[str, Any]: Response data
    """
    try:
        service = get_authenticated_service(MessagingProfilesService)
        return service.update_messaging_profile(profile_id, **request)
    except Exception as e:
        logger.error(f"Error updating messaging profile: {e}")
        raise handle_telnyx_error(e)
