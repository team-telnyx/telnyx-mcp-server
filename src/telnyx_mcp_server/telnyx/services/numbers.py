"""Telnyx phone numbers service."""

from typing import Any, Dict, List, Optional

from ...utils.logger import get_logger
from ..client import TelnyxClient

logger = get_logger(__name__)


class NumbersService:
    """Telnyx phone numbers service."""

    def __init__(self, client: Optional[TelnyxClient] = None):
        """Initialize the service.

        Args:
            client: Telnyx API client (creates a new one if not provided)
        """
        self.client = client or TelnyxClient()

    def list_phone_numbers(
        self,
        page: int = 1,
        page_size: int = 20,
        filter_tag: Optional[str] = None,
        filter_phone_number: Optional[str] = None,
        filter_status: Optional[str] = None,
        filter_country_iso_alpha2: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List phone numbers.

        Args:
            page: Page number
            page_size: Page size
            filter_tag: Filter by phone number tag
            filter_phone_number: Filter by phone number
            filter_status: Filter by phone number status
            filter_country_iso_alpha2: Filter by country ISO alpha-2 code

        Returns:
            Dict[str, Any]: Response data
        """
        params = {
            "page[number]": page,
            "page[size]": page_size,
        }

        if filter_tag:
            params["filter[tag]"] = filter_tag

        if filter_phone_number:
            params["filter[phone_number]"] = filter_phone_number

        if filter_status:
            params["filter[status]"] = filter_status

        if filter_country_iso_alpha2:
            params["filter[country_iso_alpha2]"] = filter_country_iso_alpha2

        return self.client.get("phone_numbers", params=params)

    def get_phone_number(self, id: str) -> Dict[str, Any]:
        """Get a phone number by ID.

        Args:
            id: Phone number ID as string

        Returns:
            Dict[str, Any]: Response data
        """
        return self.client.get(f"phone_numbers/{id}")

    def update_phone_number(
        self, id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a phone number.

        Args:
            id: Phone number ID as string
            data: Update data

        Returns:
            Dict[str, Any]: Response data
        """
        return self.client.patch(f"phone_numbers/{id}", data=data)

    def list_available_phone_numbers(
        self,
        page: int = 1,
        page_size: int = 20,
        filter_phone_number_starts_with: Optional[str] = None,
        filter_phone_number_ends_with: Optional[str] = None,
        filter_phone_number_contains: Optional[str] = None,
        filter_locality: Optional[str] = None,
        filter_administrative_area: Optional[str] = None,
        filter_country_code: Optional[str] = None,
        filter_features: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """List available phone numbers.

        Args:
            page: Page number
            page_size: Page size
            filter_phone_number_starts_with: Filter numbers starting with pattern
            filter_phone_number_ends_with: Filter numbers ending with pattern
            filter_phone_number_contains: Filter numbers containing pattern
            filter_locality: Filter by locality (city)
            filter_administrative_area: Filter by administrative area (state)
            filter_country_code: Filter by country code
            filter_features: Filter by features

        Returns:
            Dict[str, Any]: Response data
        """
        params = {
            "page[number]": page,
            "page[size]": page_size,
        }

        if filter_phone_number_starts_with:
            params["filter[phone_number][starts_with]"] = (
                filter_phone_number_starts_with
            )

        if filter_phone_number_ends_with:
            params["filter[phone_number][ends_with]"] = (
                filter_phone_number_ends_with
            )

        if filter_phone_number_contains:
            params["filter[phone_number][contains]"] = (
                filter_phone_number_contains
            )

        if filter_locality:
            params["filter[locality]"] = filter_locality

        if filter_administrative_area:
            params["filter[administrative_area]"] = filter_administrative_area

        if filter_country_code:
            params["filter[country_code]"] = filter_country_code

        if filter_features:
            params["filter[features]"] = ",".join(filter_features)

        return self.client.get("available_phone_numbers", params=params)

    def buy_phone_number(
        self, phone_number: str, connection_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Buy a phone number.

        Args:
            phone_number: Phone number to buy
            connection_id: Connection ID to associate with the number

        Returns:
            Dict[str, Any]: Response data
        """
        data = {"phone_numbers": [{"phone_number": phone_number}]}

        if connection_id:
            data["connection_id"] = connection_id

        return self.client.post("number_orders", data=data)

    def update_phone_number_messaging_settings(
        self,
        id: str,
        messaging_profile_id: Optional[str] = None,
        messaging_product: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update the messaging profile and/or messaging product of a phone number.

        Args:
            id: The phone number ID to update
            messaging_profile_id: Configure the messaging profile this phone number is assigned to
            messaging_product: Configure the messaging product for this number

        Returns:
            Dict[str, Any]: Response data containing the updated phone number messaging settings
        """
        data = {}

        if messaging_profile_id is not None:
            data["messaging_profile_id"] = messaging_profile_id

        if messaging_product is not None:
            data["messaging_product"] = messaging_product

        return self.client.patch(f"phone_numbers/{id}/messaging", data=data)
