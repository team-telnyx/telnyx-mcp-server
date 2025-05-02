"""Tests for the secrets manager MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

from telnyx_mcp_server.tools.secrets import (
    create_integration_secret,
    delete_integration_secret,
    list_integration_secrets,
)


@pytest.fixture
def mock_service():
    """Create a mock SecretsService."""
    service = MagicMock()
    service.list_integration_secrets.return_value = {"data": [{"id": "test-id"}]}
    service.create_integration_secret.return_value = {"data": {"id": "new-id"}}
    service.delete_integration_secret.return_value = {}
    return service


@pytest.mark.asyncio
@patch("telnyx_mcp_server.tools.secrets.get_authenticated_service")
async def test_list_integration_secrets(mock_get_service, mock_service):
    """Test the list_integration_secrets tool."""
    mock_get_service.return_value = mock_service
    
    result = await list_integration_secrets({"page": 2, "page_size": 10, "filter_type": "bearer"})
    
    mock_get_service.assert_called_once()
    mock_service.list_integration_secrets.assert_called_once_with(
        page=2, page_size=10, filter_type="bearer"
    )
    assert result == {"data": [{"id": "test-id"}]}


@pytest.mark.asyncio
@patch("telnyx_mcp_server.tools.secrets.get_authenticated_service")
async def test_create_integration_secret(mock_get_service, mock_service):
    """Test the create_integration_secret tool."""
    mock_get_service.return_value = mock_service
    
    request = {
        "identifier": "test-identifier",
        "type": "bearer",
        "token": "test-token"
    }
    
    result = await create_integration_secret(request)
    
    mock_get_service.assert_called_once()
    mock_service.create_integration_secret.assert_called_once_with(**request)
    assert result == {"data": {"id": "new-id"}}


@pytest.mark.asyncio
@patch("telnyx_mcp_server.tools.secrets.get_authenticated_service")
async def test_delete_integration_secret(mock_get_service, mock_service):
    """Test the delete_integration_secret tool."""
    mock_get_service.return_value = mock_service
    
    result = await delete_integration_secret(id="test-id")
    
    mock_get_service.assert_called_once()
    mock_service.delete_integration_secret.assert_called_once_with(id="test-id")
    assert result == {}