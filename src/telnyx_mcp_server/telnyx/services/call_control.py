"""Telnyx call control service."""

from typing import Any, Dict, Optional

from ...utils.logger import get_logger
from ..client import TelnyxClient

logger = get_logger(__name__)


class CallControlService:
    """Service for managing Telnyx calls."""

    def __init__(self, client: Optional[TelnyxClient] = None):
        """Initialize the service with a Telnyx client."""
        self.client = client or TelnyxClient()

    def list_call_control_applications(
        self,
        request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """List call control applications.

        Args:
            request: Request parameters for listing call control applications

        Returns:
            Dict[str, Any]: Response data
        """
        params = {
            "page[number]": request.get("page", 1),
            "page[size]": request.get("page_size", 20),
        }

        if request.get("filter_application_name_contains"):
            params["filter[application_name][contains]"] = request[
                "filter_application_name_contains"
            ]

        if request.get("filter_outbound_voice_profile_id"):
            params["filter[outbound.outbound_voice_profile_id]"] = request[
                "filter_outbound_voice_profile_id"
            ]

        if request.get("sort"):
            params["sort"] = request["sort"]

        response = self.client.get("call_control_applications", params=params)
        if isinstance(response, dict):
            return response
        return response.json()

    def get_call_control_application(
        self,
        request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Retrieve a specific call control application.

        Args:
            request: Request parameters containing the call control application ID

        Returns:
            Dict[str, Any]: Response data
        """
        application_id = request.get("id")
        response = self.client.get(f"call_control_applications/{application_id}")
        if isinstance(response, dict):
            return response
        return response.json()

    def create_call_control_application(
        self,
        request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a call control application.

        Args:
            request: Request parameters for creating a call control application

        Returns:
            Dict[str, Any]: Response data
        """
        # Create a copy of the request to avoid modifying the original
        data = request.copy()

        response = self.client.post("call_control_applications", data=data)
        if isinstance(response, dict):
            return response
        return response.json()

    def make_call(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a call.

        Args:
            data: Call request parameters
                  Note: connection_id and call_control_application_id are the same thing,
                  either can be used to specify the application for the call.

        Returns:
            Dict[str, Any]: Response data
        """

        # Rename from_ to from as required by the API
        if "from_" in data:
            data["from"] = data.pop("from_")

        response = self.client.post("/calls", data=data)
        return response

    def hangup(self, call_control_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Hang up a call.

        Args:
            call_control_id: Call control ID
            data: Hangup request parameters

        Returns:
            Dict[str, Any]: Response data
        """
        response = self.client.post(
            f"/calls/{call_control_id}/actions/hangup", data=data
        )
        return response

    def playback_start(
        self, call_control_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Start audio playback on a call.

        Args:
            call_control_id: Call control ID
            data: Playback request parameters

        Returns:
            Dict[str, Any]: Response data
        """
        response = self.client.post(
            f"/calls/{call_control_id}/actions/playback_start", data=data
        )
        return response

    def playback_stop(
        self, call_control_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Stop audio playback on a call.

        Args:
            call_control_id: Call control ID
            data: Playback stop request parameters

        Returns:
            Dict[str, Any]: Response data
        """
        response = self.client.post(
            f"/calls/{call_control_id}/actions/playback_stop", data=data
        )
        return response

    def send_dtmf(self, call_control_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send DTMF tones on a call.

        Args:
            call_control_id: Call control ID
            data: DTMF request parameters

        Returns:
            Dict[str, Any]: Response data
        """
        response = self.client.post(
            f"/calls/{call_control_id}/actions/send_dtmf", data=data
        )
        return response

    def speak(self, call_control_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Speak text on a call.

        Args:
            call_control_id: Call control ID
            data: Speak request parameters

        Returns:
            Dict[str, Any]: Response data
        """
        response = self.client.post(
            f"/calls/{call_control_id}/actions/speak", data=data
        )
        return response

    def transfer(self, call_control_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transfer a call.

        Args:
            call_control_id: Call control ID
            data: Transfer request parameters

        Returns:
            Dict[str, Any]: Response data
        """

        # Rename from_ to from as required by the API
        if "from_" in data:
            data["from"] = data.pop("from_")

        response = self.client.post(
            f"/calls/{call_control_id}/actions/transfer", data=data
        )
        return response
