"""Tests for the embeddings MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

from telnyx_mcp_server.tools.embeddings import (
    create_embeddings,
    embed_url,
    list_embedded_buckets,
)


@pytest.fixture
def mock_service():
    """Create a mock EmbeddingsService."""
    service = MagicMock()
    service.list_embedded_buckets.return_value = {"data": [{"id": "test-bucket-id"}]}
    service.embed_url.return_value = {"data": {"bucket": "test-bucket"}}
    service.create_embeddings.return_value = {"data": {"embeddings": [[0.1, 0.2, 0.3]]}}
    return service


@pytest.mark.asyncio
@patch("telnyx_mcp_server.tools.embeddings.get_authenticated_service")
async def test_list_embedded_buckets(mock_get_service, mock_service):
    """Test the list_embedded_buckets tool."""
    mock_get_service.return_value = mock_service

    result = await list_embedded_buckets({"page": 2, "page_size": 10})

    mock_get_service.assert_called_once()
    mock_service.list_embedded_buckets.assert_called_once_with(page=2, page_size=10)
    assert result == {"data": [{"id": "test-bucket-id"}]}


@pytest.mark.asyncio
@patch("telnyx_mcp_server.tools.embeddings.get_authenticated_service")
async def test_embed_url(mock_get_service, mock_service):
    """Test the embed_url tool."""
    mock_get_service.return_value = mock_service

    request = {"url": "https://example.com", "bucket": "my-bucket"}

    result = await embed_url(request)

    mock_get_service.assert_called_once()
    mock_service.embed_url.assert_called_once_with(**request)
    assert result == {"data": {"bucket": "test-bucket"}}


@pytest.mark.asyncio
@patch("telnyx_mcp_server.tools.embeddings.get_authenticated_service")
async def test_create_embeddings(mock_get_service, mock_service):
    """Test the create_embeddings tool."""
    mock_get_service.return_value = mock_service

    request = {"texts": ["Hello world", "Test text"], "model": "text-embedding-ada-002"}

    result = await create_embeddings(request)

    mock_get_service.assert_called_once()
    mock_service.create_embeddings.assert_called_once_with(**request)
    assert result == {"data": {"embeddings": [[0.1, 0.2, 0.3]]}}
