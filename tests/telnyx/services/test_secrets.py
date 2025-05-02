"""Tests for the Telnyx secrets manager service."""

from unittest.mock import MagicMock

import pytest

from telnyx_mcp_server.telnyx.services.secrets import SecretsService


@pytest.fixture
def mock_client():
    """Create a mock Telnyx client."""
    client = MagicMock()
    client.get.return_value = {"data": [{"id": "test-id"}]}
    client.post.return_value = {"data": {"id": "new-id"}}
    client.delete.return_value = {}
    return client


def test_list_integration_secrets(mock_client):
    """Test listing integration secrets."""
    service = SecretsService(client=mock_client)
    result = service.list_integration_secrets(
        page=2, page_size=10, filter_type="bearer"
    )

    mock_client.get.assert_called_once_with(
        "integration_secrets",
        params={"page[number]": 2, "page[size]": 10, "filter[type]": "bearer"},
    )
    assert result == {"data": [{"id": "test-id"}]}


def test_create_integration_secret_bearer(mock_client):
    """Test creating a bearer integration secret."""
    service = SecretsService(client=mock_client)
    result = service.create_integration_secret(
        request={
            "identifier": "test-identifier",
            "type": "bearer",
            "token": "test-token",
        }
    )

    mock_client.post.assert_called_once_with(
        "integration_secrets",
        data={
            "identifier": "test-identifier",
            "type": "bearer",
            "token": "test-token",
        },
    )
    assert result == {"data": {"id": "new-id"}}


def test_create_integration_secret_basic(mock_client):
    """Test creating a basic integration secret."""
    service = SecretsService(client=mock_client)
    result = service.create_integration_secret(
        request={
            "identifier": "test-identifier",
            "type": "basic",
            "username": "test-user",
            "password": "test-pass",
        }
    )

    mock_client.post.assert_called_once_with(
        "integration_secrets",
        data={
            "identifier": "test-identifier",
            "type": "basic",
            "username": "test-user",
            "password": "test-pass",
        },
    )
    assert result == {"data": {"id": "new-id"}}


def test_delete_integration_secret(mock_client):
    """Test deleting an integration secret."""
    service = SecretsService(client=mock_client)
    result = service.delete_integration_secret(id="test-id")

    mock_client.delete.assert_called_once_with("integration_secrets/test-id")
    assert result == {}
