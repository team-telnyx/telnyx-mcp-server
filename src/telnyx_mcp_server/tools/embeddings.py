"""Embeddings related MCP tools."""

from typing import Any, Dict

from ..mcp import mcp
from ..telnyx.services.embeddings import EmbeddingsService
from ..utils.error_handler import handle_telnyx_error
from ..utils.logger import get_logger
from ..utils.service import get_authenticated_service

logger = get_logger(__name__)


@mcp.tool()
async def list_embedded_buckets() -> Dict[str, Any]:
    """List user embedded buckets.

    Returns:
        Dict[str, Any]: Response data eg:
        {
            "data": {
                "buckets": [
                "string"
                ]
            }
        }
    """
    try:
        service = get_authenticated_service(EmbeddingsService)
        return service.list_embedded_buckets()
    except Exception as e:
        logger.error(f"Error listing embedded buckets: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def embed_url(request: Dict[str, Any]) -> Dict[str, Any]:
    """Scrape and embed a given URL. For a given website, this tool will scrape
    the content of the pages and save the content in a new bucket. That bucket will
    be automatically embedded.

    Args:
        url: Required. URL to be scraped and embedded.

    Returns:
        Dict[str, Any]: Response data containing bucket information
    """
    try:
        service = get_authenticated_service(EmbeddingsService)
        return service.embed_url(request)
    except Exception as e:
        logger.error(f"Error embedding URL: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def create_embeddings(request: Dict[str, Any]) -> Dict[str, Any]:
    """Embed a bucket that containe files.

    Args:
        bucket_name: Required. Bucket Name. The bucket must exist (string)
        document_chunk_size: Optional. Document Chunk Size (integer)
        document_chunk_overlap_size: Optional. Document Chunk Overlap Size (integer)
        embedding_model: Optional. Supported models (thenlper/gte-large,
        intfloat/multilingual-e5-large, sentence-transformers/all-mpnet-base-v2)
        to vectorize and embed documents.
        loader: Optional. (default, intercom) (string)

    Agent should prefer only rely on required fields unless user explicitly
    provides values for optional fields.

    Returns:
        Dict[str, Any]: Response data containing the embeddings
    """
    try:
        service = get_authenticated_service(EmbeddingsService)
        return service.create_embeddings(request)
    except Exception as e:
        logger.error(f"Error creating embeddings: {e}")
        raise handle_telnyx_error(e)
