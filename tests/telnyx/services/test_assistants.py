"""Tests for the Telnyx Assistants service."""

from unittest.mock import MagicMock

import pytest

from telnyx_mcp_server.telnyx.services.assistants import AssistantsService


class TestAssistantsService:
    """Tests for the AssistantsService class."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Telnyx client."""
        mock = MagicMock()
        mock.post.return_value = {
            "id": "test-assistant",
            "name": "Test Assistant",
        }
        return mock

    def test_create_assistant_hardcoded_values(self, mock_client):
        """Test that create_assistant hardcodes voice settings and enabled features."""
        # Setup
        service = AssistantsService(mock_client)
        request = {
            "name": "Test Assistant",
            "instructions": "Test instructions",
            # These values should be overridden by the hardcoded values
            "voice_settings": {
                "voice": "some-other-voice",
                "api_key_ref": "some-api-key",
            },
            "enabled_features": ["messaging"],
        }

        # Execute
        service.create_assistant(request)

        # Verify
        # Get the actual request that was sent to the API
        args, kwargs = mock_client.post.call_args

        # Verify the endpoint
        assert args[0] == "/ai/assistants"

        # Verify the request data
        sent_request = kwargs["data"]
        assert (
            sent_request["voice_settings"]["voice"]
            == "Telnyx.KokoroTTS.af_heart"
        )
        assert sent_request["voice_settings"]["api_key_ref"] is None
        assert sent_request["enabled_features"] == ["telephony"]

        # Make sure original values were preserved
        assert sent_request["name"] == "Test Assistant"
        assert sent_request["instructions"] == "Test instructions"

    def test_update_assistant_removes_hardcoded_fields(self, mock_client):
        """Test that update_assistant removes voice settings and enabled features from the request."""
        # Setup
        service = AssistantsService(mock_client)
        assistant_id = "test-assistant-id"
        request = {
            "name": "Updated Assistant",
            "instructions": "Updated instructions",
            # These values should be removed from the request
            "voice_settings": {
                "voice": "some-voice",
                "api_key_ref": "some-api-key",
            },
            "enabled_features": ["messaging", "telephony"],
        }

        # Execute
        service.update_assistant(assistant_id, request)

        # Verify
        # Get the actual request that was sent to the API
        args, kwargs = mock_client.post.call_args

        # Verify the endpoint
        assert args[0] == f"/ai/assistants/{assistant_id}"

        # Verify the request data
        sent_request = kwargs["data"]
        # These fields should be removed
        assert "voice_settings" not in sent_request
        assert "enabled_features" not in sent_request

        # Other fields should be preserved
        assert sent_request["name"] == "Updated Assistant"
        assert sent_request["instructions"] == "Updated instructions"
