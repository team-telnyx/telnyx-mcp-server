"""Tests for the Telnyx embeddings service."""

from unittest.mock import MagicMock

import pytest

from telnyx_mcp_server.telnyx.services.embeddings import EmbeddingsService


@pytest.fixture
def mock_client():
    """Create a mock Telnyx client."""
    client = MagicMock()
    client.get.return_value = {"data": [{"id": "test-bucket-id"}]}
    return client


def test_list_embedded_buckets(mock_client):
    """Test listing embedded buckets."""
    service = EmbeddingsService(client=mock_client)
    result = service.list_embedded_buckets()

    mock_client.get.assert_called_once_with(
        "ai/embeddings/buckets",
    )
    assert result == {"data": [{"id": "test-bucket-id"}]}


def test_embed_url_without_bucket(mock_client):
    """Test embedding a URL without specifying a bucket."""
    service = EmbeddingsService(client=mock_client)
    _ = service.embed_url(request={"url": "https://example.com"})

    mock_client.post.assert_called_once_with(
        "ai/embeddings/url",
        data={"url": "https://example.com"},
    )


def test_create_embeddings_basic(mock_client):
    """Test creating embeddings without specifying a model."""
    service = EmbeddingsService(client=mock_client)
    request = {
        "bucket_name": "test-bucket",
    }
    _ = service.create_embeddings(request=request)

    mock_client.post.assert_called_once_with(
        "ai/embeddings",
        data=request,
    )


def test_create_embeddings_all_fields(mock_client):
    """Test creating embeddings with a specified model."""
    service = EmbeddingsService(client=mock_client)
    request = {
        "bucket_name": "test-bucket",
        "document_chunk_size": 100,
        "document_chunk_overlap_size": 20,
        "embedding_model": "thenlper/gte-large",
    }
    result = service.create_embeddings(request=request)

    mock_client.post.assert_called_once_with(
        "ai/embeddings",
        data=request,
    )
