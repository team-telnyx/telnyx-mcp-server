"""Test script to verify ID parameter validation for phone number tools."""

import logging
import sys
from typing import Any, Dict, Optional

import httpx
import pytest
from pytest_mock import MockerFixture

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("id-validation-test")

# Server URL
SERVER_URL = "http://localhost:8000/mcp"


class MockResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json_data = json_data or {}

    def json(self):
        return self._json_data


@pytest.fixture
def mock_httpx_client(mocker: MockerFixture):
    """Mock httpx.AsyncClient"""
    mock_client = mocker.AsyncMock()
    mock_client.post.return_value = MockResponse(
        json_data={
            "jsonrpc": "2.0",
            "result": {
                "data": [
                    {
                        "id": "12345",
                        "phone_number": "+1234567890",
                        "status": "active",
                    }
                ]
            },
            "id": "test-request",
        }
    )
    mocker.patch("httpx.AsyncClient", return_value=mock_client)
    return mock_client


async def call_tool(
    tool_name: str,
    parameters: Dict[str, Any],
    request_id: Optional[str] = None,
    client=None,
) -> Dict[str, Any]:
    """Call a tool on the MCP server.

    Args:
        tool_name: Name of the tool to call
        parameters: Tool parameters
        request_id: Request ID (optional)
        client: Optional httpx client (for testing)

    Returns:
        Dict[str, Any]: Response data
    """
    request_id = request_id or "test-request"
    request_data = {
        "jsonrpc": "2.0",
        "method": "callTool",
        "params": {"name": tool_name, "parameters": parameters},
        "id": request_id,
    }

    logger.info(f"Calling tool: {tool_name} with parameters: {parameters}")
    if client:
        response = await client.post(SERVER_URL, json=request_data)
    else:
        async with httpx.AsyncClient() as client:
            response = await client.post(SERVER_URL, json=request_data)

    response_data = response.json()
    logger.info(f"Response: {response_data}")
    return response_data


@pytest.mark.asyncio
async def test_list_phone_numbers(mock_httpx_client) -> None:
    """Test list_phone_numbers tool."""
    logger.info("\n=== Testing list_phone_numbers ===")
    response = await call_tool(
        "list_phone_numbers",
        {"page": 1, "page_size": 5},
        "list-phone-numbers-request",
        client=mock_httpx_client,
    )
    assert "error" not in response
    assert "result" in response
    assert "data" in response["result"]


@pytest.mark.asyncio
async def test_get_phone_number_string_id(mock_httpx_client) -> None:
    """Test get_phone_number tool with string ID."""
    logger.info("\n=== Testing get_phone_number with string ID ===")
    phone_number_id = "12345"

    response = await call_tool(
        "get_phone_number",
        {"id": str(phone_number_id)},
        "get-phone-number-string-request",
        client=mock_httpx_client,
    )
    assert "error" not in response
    assert "result" in response


@pytest.mark.asyncio
async def test_get_phone_number_numeric_id(mock_httpx_client) -> None:
    """Test get_phone_number tool with numeric ID."""
    logger.info("\n=== Testing get_phone_number with numeric ID ===")
    phone_number_id = 12345

    response = await call_tool(
        "get_phone_number",
        {"id": phone_number_id},
        "get-phone-number-numeric-request",
        client=mock_httpx_client,
    )
    assert "error" not in response
    assert "result" in response


@pytest.mark.asyncio
async def test_update_phone_number_string_id(mock_httpx_client) -> None:
    """Test update_phone_number tool with string ID."""
    logger.info("\n=== Testing update_phone_number with string ID ===")
    phone_number_id = "12345"

    response = await call_tool(
        "update_phone_number",
        {"id": str(phone_number_id), "data": {"tags": ["test-tag"]}},
        "update-phone-number-string-request",
        client=mock_httpx_client,
    )
    assert "error" not in response
    assert "result" in response


@pytest.mark.asyncio
async def test_update_phone_number_numeric_id(mock_httpx_client) -> None:
    """Test update_phone_number tool with numeric ID."""
    logger.info("\n=== Testing update_phone_number with numeric ID ===")
    phone_number_id = 12345

    response = await call_tool(
        "update_phone_number",
        {"id": phone_number_id, "data": {"tags": ["test-tag"]}},
        "update-phone-number-numeric-request",
        client=mock_httpx_client,
    )
    assert "error" not in response
    assert "result" in response
