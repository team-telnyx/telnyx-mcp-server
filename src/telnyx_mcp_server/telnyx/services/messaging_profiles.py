"""Telnyx messaging profiles service."""

from typing import Any, Dict, List, Optional

from ...utils.logger import get_logger
from ..client import TelnyxClient

logger = get_logger(__name__)


class MessagingProfilesService:
    """Telnyx messaging profiles service."""

    def __init__(self, client: Optional[TelnyxClient] = None):
        """Initialize the service.

        Args:
            client: Telnyx API client (creates a new one if not provided)
        """
        self.client = client or TelnyxClient()

    def list_messaging_profiles(
        self,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        filter_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List messaging profiles.

        Args:
            page: The page number to load
            page_size: The size of the page
            filter_name: Filter by name

        Returns:
            Dict[str, Any]: Response data containing list of messaging profiles
        """
        params = {}
        if page is not None:
            params["page[number]"] = page
        if page_size is not None:
            params["page[size]"] = page_size
        if filter_name is not None:
            params["filter[name]"] = filter_name

        return self.client.get("messaging_profiles", params=params)

    def create_messaging_profile(
        self,
        name: str,
        whitelisted_destinations: List[str],
        enabled: Optional[bool] = None,
        webhook_url: Optional[str] = None,
        webhook_failover_url: Optional[str] = None,
        webhook_api_version: Optional[str] = None,
        number_pool_settings: Optional[dict] = None,
        url_shortener_settings: Optional[dict] = None,
        alpha_sender: Optional[str] = None,
        daily_spend_limit: Optional[str] = None,
        daily_spend_limit_enabled: Optional[bool] = None,
        mms_fall_back_to_sms: Optional[bool] = None,
        mms_transcoding: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Create a messaging profile.

        Args:
            name: A user friendly name for the messaging profile
            whitelisted_destinations: Destinations to which the messaging profile is allowed to send
            enabled: Specifies whether the messaging profile is enabled or not
            webhook_url: The URL where webhooks related to this messaging profile will be sent
            webhook_failover_url: The failover URL where webhooks related to this messaging profile will be sent
            webhook_api_version: Determines which webhook format will be used
            number_pool_settings: Number Pool settings
            url_shortener_settings: URL shortener settings
            alpha_sender: The alphanumeric sender ID
            daily_spend_limit: The maximum amount of money that can be spent
            daily_spend_limit_enabled: Whether to enforce the daily spend limit
            mms_fall_back_to_sms: Enables SMS fallback for MMS messages
            mms_transcoding: Enables automated resizing of MMS media

        Returns:
            Dict[str, Any]: Response data containing the created messaging profile
        """
        data = {
            "name": name,
            "whitelisted_destinations": whitelisted_destinations,
        }

        if enabled is not None:
            data["enabled"] = enabled
        if webhook_url is not None:
            data["webhook_url"] = webhook_url
        if webhook_failover_url is not None:
            data["webhook_failover_url"] = webhook_failover_url
        if webhook_api_version is not None:
            data["webhook_api_version"] = webhook_api_version
        if number_pool_settings is not None:
            data["number_pool_settings"] = number_pool_settings
        if url_shortener_settings is not None:
            data["url_shortener_settings"] = url_shortener_settings
        if alpha_sender is not None:
            data["alpha_sender"] = alpha_sender
        if daily_spend_limit is not None:
            data["daily_spend_limit"] = daily_spend_limit
        if daily_spend_limit_enabled is not None:
            data["daily_spend_limit_enabled"] = daily_spend_limit_enabled
        if mms_fall_back_to_sms is not None:
            data["mms_fall_back_to_sms"] = mms_fall_back_to_sms
        if mms_transcoding is not None:
            data["mms_transcoding"] = mms_transcoding

        return self.client.post("messaging_profiles", data=data)

    def get_messaging_profile(self, profile_id: str) -> Dict[str, Any]:
        """Retrieve a messaging profile by ID.

        Args:
            profile_id: The ID of the messaging profile to retrieve

        Returns:
            Dict[str, Any]: Response data containing messaging profile details
        """
        return self.client.get(f"messaging_profiles/{profile_id}")

    def update_messaging_profile(
        self,
        profile_id: str,
        name: Optional[str] = None,
        enabled: Optional[bool] = None,
        webhook_url: Optional[str] = None,
        webhook_failover_url: Optional[str] = None,
        webhook_api_version: Optional[str] = None,
        whitelisted_destinations: Optional[List[str]] = None,
        v1_secret: Optional[str] = None,
        number_pool_settings: Optional[dict] = None,
        url_shortener_settings: Optional[dict] = None,
        alpha_sender: Optional[str] = None,
        daily_spend_limit: Optional[str] = None,
        daily_spend_limit_enabled: Optional[bool] = None,
        mms_fall_back_to_sms: Optional[bool] = None,
        mms_transcoding: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update a messaging profile.

        Args:
            profile_id: The ID of the messaging profile to update
            name: A user friendly name for the messaging profile
            enabled: Specifies whether the messaging profile is enabled or not
            webhook_url: The URL where webhooks related to this messaging profile will be sent
            webhook_failover_url: The failover URL where webhooks related to this messaging profile will be sent
            webhook_api_version: Determines which webhook format will be used
            whitelisted_destinations: Destinations to which the messaging profile is allowed to send
            v1_secret: Secret used to authenticate with v1 endpoints
            number_pool_settings: Number Pool settings
            url_shortener_settings: URL shortener settings
            alpha_sender: The alphanumeric sender ID
            daily_spend_limit: The maximum amount of money that can be spent
            daily_spend_limit_enabled: Whether to enforce the daily spend limit
            mms_fall_back_to_sms: Enables SMS fallback for MMS messages
            mms_transcoding: Enables automated resizing of MMS media

        Returns:
            Dict[str, Any]: Response data containing the updated messaging profile
        """
        data = {}

        if name is not None:
            data["name"] = name
        if enabled is not None:
            data["enabled"] = enabled
        if webhook_url is not None:
            data["webhook_url"] = webhook_url
        if webhook_failover_url is not None:
            data["webhook_failover_url"] = webhook_failover_url
        if webhook_api_version is not None:
            data["webhook_api_version"] = webhook_api_version
        if whitelisted_destinations is not None:
            data["whitelisted_destinations"] = whitelisted_destinations
        if v1_secret is not None:
            data["v1_secret"] = v1_secret
        if number_pool_settings is not None:
            data["number_pool_settings"] = number_pool_settings
        if url_shortener_settings is not None:
            data["url_shortener_settings"] = url_shortener_settings
        if alpha_sender is not None:
            data["alpha_sender"] = alpha_sender
        if daily_spend_limit is not None:
            data["daily_spend_limit"] = daily_spend_limit
        if daily_spend_limit_enabled is not None:
            data["daily_spend_limit_enabled"] = daily_spend_limit_enabled
        if mms_fall_back_to_sms is not None:
            data["mms_fall_back_to_sms"] = mms_fall_back_to_sms
        if mms_transcoding is not None:
            data["mms_transcoding"] = mms_transcoding

        return self.client.patch(f"messaging_profiles/{profile_id}", data=data)
