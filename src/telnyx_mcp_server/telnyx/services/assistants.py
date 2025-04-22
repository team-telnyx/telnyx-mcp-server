"""Telnyx AI Assistants service."""

from typing import Any, Dict, Optional

from ..client import TelnyxClient


class AssistantsService:
    """Service for managing Telnyx AI Assistants."""

    def __init__(self, client: TelnyxClient) -> None:
        """Initialize the service.

        Args:
            client: Telnyx API client
        """
        self.client = client

    def create_assistant(
        self,
        request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a new AI Assistant.

        Args:
            request: Assistant creation request data

        Returns:
            Dict[str, Any]: Created assistant data
        """
        # Hard code voice settings and enabled features
        request["voice_settings"] = {
            "voice": "Telnyx.KokoroTTS.af_heart",
            "api_key_ref": None
        }
        request["enabled_features"] = ["telephony"]
        
        response = self.client.post("/ai/assistants", data=request)
        return response

    def list_assistants(self) -> Dict[str, Any]:
        """List all AI Assistants.

        Returns:
            Dict[str, Any]: List of assistants
        """
        response = self.client.get("/ai/assistants")
        return response

    def get_assistant(
        self,
        assistant_id: str,
        fetch_dynamic_variables_from_webhook: Optional[bool] = None,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        call_control_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get an AI Assistant by ID.

        Args:
            assistant_id: Assistant ID
            fetch_dynamic_variables_from_webhook: Whether to fetch dynamic variables from webhook
            from_: From parameter for dynamic variables
            to: To parameter for dynamic variables
            call_control_id: Call control ID for dynamic variables

        Returns:
            Dict[str, Any]: Assistant data
        """
        params: Dict[str, Any] = {}
        if fetch_dynamic_variables_from_webhook is not None:
            params["fetch_dynamic_variables_from_webhook"] = (
                fetch_dynamic_variables_from_webhook
            )
        if from_ is not None:
            params["from"] = from_
        if to is not None:
            params["to"] = to
        if call_control_id is not None:
            params["call_control_id"] = call_control_id

        response = self.client.get(
            f"/ai/assistants/{assistant_id}", params=params
        )
        return response

    def update_assistant(
        self,
        assistant_id: str,
        request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update an AI Assistant.

        Args:
            assistant_id: Assistant ID
            request: Assistant update request data

        Returns:
            Dict[str, Any]: Updated assistant data
        """
        # Hard code voice settings and enabled features
        if "voice_settings" in request:
            del request["voice_settings"]
            
        if "enabled_features" in request:
            del request["enabled_features"]
            
        response = self.client.post(
            f"/ai/assistants/{assistant_id}",
            data=request,
        )
        return response

    def delete_assistant(self, assistant_id: str) -> Dict[str, Any]:
        """Delete an AI Assistant.

        Args:
            assistant_id: Assistant ID

        Returns:
            Dict[str, Any]: Deletion response containing id, object, and deleted status
        """
        response = self.client.delete(f"/ai/assistants/{assistant_id}")
        return response

    def get_assistant_texml(self, assistant_id: str) -> str:
        """Get an assistant's TEXML by ID.

        Args:
            assistant_id: Assistant ID

        Returns:
            str: Assistant TEXML content
        """
        response = self.client.get(f"/ai/assistants/{assistant_id}/texml")
        return response
        
    def start_assistant_call(self, default_texml_app_id: str, to: str, from_: str) -> Dict[str, Any]:
        """Start a call using the assistant's TeXML application.
        
        Args:
            default_texml_app_id: The assistant's default TeXML application ID
            to: Destination number to call
            from_: Source number to call from
            
        Returns:
            Dict[str, Any]: Response data
        """
        data = {
            "To": to,
            "From": from_
        }
        response = self.client.post(f"/texml/calls/{default_texml_app_id}", data=data)
        return response
