"""Tests for the webhook server."""

import json
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest

from telnyx_mcp_server.config import settings
from telnyx_mcp_server.webhook.server import webhook_app


@pytest.fixture
def client():
    """Create a test client for the webhook server."""
    return TestClient(webhook_app)


def test_webhook_handler_valid_payload(client):
    """Test that the webhook handler accepts valid payloads."""
    # Sample Telnyx webhook payload
    payload = {
        "data": {
            "event_type": "call.initiated",
            "id": "0ccc7b54-4df3-4bca-a65a-3da1ecc777f0",
            "occurred_at": "2023-01-01T00:00:00Z",
            "payload": {
                "call_control_id": "v2:123456789",
                "call_leg_id": "123456789",
                "call_session_id": "123456789",
                "client_state": None,
                "direction": "outgoing",
                "from": "+15551234567",
                "to": "+15557654321",
            },
        },
        "meta": {
            "attempt": 1,
            "delivered_to": "https://example.com/webhooks",
        },
    }

    # Mock headers
    headers = {
        "telnyx-signature-ed25519": "test-signature",
        "telnyx-timestamp": "1609459200",
    }

    # Send the request
    response = client.post(
        settings.webhook_path,
        json=payload,
        headers=headers,
    )

    # Check the response
    assert response.status_code == 200


def test_webhook_handler_empty_payload(client):
    """Test that the webhook handler accepts empty payloads."""
    # Send the request with an empty body
    response = client.post(settings.webhook_path)

    # Check the response
    assert response.status_code == 200


def test_webhook_handler_invalid_json(client):
    """Test that the webhook handler rejects invalid JSON."""
    # Send the request with invalid JSON
    response = client.post(
        settings.webhook_path,
        content=b"{invalid json",
    )

    # Check the response
    assert response.status_code == 400
    assert "Invalid JSON payload" in response.json()["detail"]


def test_webhook_handler_payload_too_large(client):
    """Test that the webhook handler rejects payloads that are too large."""
    # Create a large payload
    large_payload = {"data": "x" * (settings.webhook_max_body_size + 1)}

    # Mock the content-length header
    headers = {
        "content-length": str(len(json.dumps(large_payload))),
    }

    # Send the request
    response = client.post(
        settings.webhook_path,
        json=large_payload,
        headers=headers,
    )

    # Check the response
    assert response.status_code == 413
    assert "Request body too large" in response.json()["detail"]


@patch("telnyx_mcp_server.webhook.server.logger")
def test_webhook_handler_logs_payload(mock_logger, client):
    """Test that the webhook handler logs the payload."""
    # Sample Telnyx webhook payload
    payload = {
        "data": {
            "event_type": "call.initiated",
            "id": "0ccc7b54-4df3-4bca-a65a-3da1ecc777f0",
        },
    }

    # Send the request
    response = client.post(
        settings.webhook_path,
        json=payload,
    )

    # Check that the logger was called
    mock_logger.debug.assert_called()
    mock_logger.info.assert_called_with(
        "Received webhook event: call.initiated"
    )

    # Check the response
    assert response.status_code == 200
