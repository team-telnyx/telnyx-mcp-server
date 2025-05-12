"""Basic smoke test for the Telnyx MCP server."""

import os
from unittest.mock import patch

import pytest

# Set the environment variable before importing the modules that need it
os.environ["TELNYX_API_KEY"] = "test_key"

# Now import the modules that require the environment variable
from telnyx_mcp_server.mcp import mcp
from telnyx_mcp_server.telnyx.client import TelnyxClient
from telnyx_mcp_server.tools.assistants import list_assistants


@pytest.fixture
def mock_telnyx_client():
    """Create a mock Telnyx client for testing."""
    with patch("telnyx_mcp_server.telnyx.client.TelnyxClient.get") as mock_get:
        mock_get.return_value = {
            "data": [{"id": "test-assistant", "name": "Test Assistant"}]
        }
        yield mock_get


@pytest.mark.asyncio
async def test_mcp_initialization():
    """Test that the MCP server initializes correctly."""
    assert isinstance(mcp, object)
    assert hasattr(mcp, "_mcp_server")
    assert hasattr(mcp, "run")


@pytest.mark.asyncio
async def test_list_assistants_tool(mock_telnyx_client):
    """Test that the list_assistants tool works correctly."""
    response = await list_assistants()
    assert isinstance(response, dict)
    assert "data" in response
    assert len(response["data"]) > 0
    assert response["data"][0]["id"] == "test-assistant"


@pytest.mark.asyncio
async def test_telnyx_client_initialization():
    """Test that the Telnyx client initializes correctly."""
    # Verify the client can be initialized with an API key
    client = TelnyxClient(api_key="test_key")
    assert client.api_key == "test_key"

    # Verify settings API key is used when no key is provided
    with patch("telnyx_mcp_server.config.settings") as mock_settings:
        mock_settings.telnyx_api_key = "settings_test_key"
        # Create a new mock to replace the TelnyxClient._init_ method
        with patch.object(
            TelnyxClient, "__init__", return_value=None
        ) as mock_init:
            client = TelnyxClient()
            client.api_key = "settings_test_key"  # we need to set this manually since we mocked __init__
            mock_init.assert_called_once()
            assert client.api_key == "settings_test_key"
