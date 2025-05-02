"""Cloud storage related MCP tools."""

import os
from typing import Any, Dict, List

from ..mcp import mcp
from ..telnyx.services.cloud_storage import BucketInfo, CloudStorageService
from ..utils.error_handler import handle_telnyx_error
from ..utils.logger import get_logger

logger = get_logger(__name__)


def instantiate_cloud_storage() -> CloudStorageService:
    api_key = os.getenv("TELNYX_API_KEY", "")
    if not api_key:
        raise ValueError("TELNYX_API_KEY environment variable must be set")
    return CloudStorageService(
        access_key_id=api_key,
        secret_access_key=api_key,
    )


@mcp.tool()
async def cloud_storage_create_bucket(request: Dict[str, Any]) -> str:
    """Create a new bucket.

    Args:
        bucket_name: Required. Name of the bucket to create
        region: Required. Region to create the bucket in (us-east-1, us-west-1, us-central-1)
    Returns:
        str: `Success!!` if it uploaded, otherwise returns an exception message
    """
    try:
        cloud_storage_service = instantiate_cloud_storage()
        if not cloud_storage_service:
            raise RuntimeError(f"Cloud storage service not initialized")
        return cloud_storage_service.create_bucket(
            bucket_name=request["bucket_name"], region=request.get("region")
        )
    except Exception as e:
        logger.error(f"Error creating bucket: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def cloud_storage_list_buckets() -> List[BucketInfo]:
    """List all buckets across all regions.

    Returns:
        List[Dict[str, str]]: List of dictionaries containing bucket information:
            - name: Name of the bucket
            - region: Region where the bucket is located
    """
    try:
        cloud_storage_service = instantiate_cloud_storage()
        if not cloud_storage_service:
            raise RuntimeError(f"Cloud storage service not initialized")
        return cloud_storage_service.list_buckets()
    except Exception as e:
        logger.error(f"Error listing buckets: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def cloud_storage_upload_file(request: Dict[str, Any]) -> str:
    """Upload a file to cloud storage.

    Args:
        absolute_file_path: Required. Absolute File Path to the file to upload
        object_name: Optional. Name to give the object in storage (defaults to file name)
        bucket_name: Optional. Bucket to upload to (defaults to instance default)
    Returns:
        str: `Success!!` if it uploaded, otherwise returns an exception message
    """
    try:
        cloud_storage_service = instantiate_cloud_storage()
        if not cloud_storage_service:
            raise RuntimeError(f"Cloud storage service not initialized")
        return cloud_storage_service.upload_file(
            file_path=request["absolute_file_path"],
            object_name=request.get("object_name"),
            bucket_name=request.get("bucket_name"),
        )
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def cloud_storage_download_file(request: Dict[str, Any]) -> str:
    """Download a file from cloud storage.

    Args:
        object_name: Required. Name of the object to download
        file_path: Required. Path where to save the downloaded file
        bucket_name: Optional. Bucket to download from (defaults to instance default)
    Returns:
        str: 'Success' if the file was downloaded successfully
    """
    try:
        cloud_storage_service = instantiate_cloud_storage()
        if not cloud_storage_service:
            raise RuntimeError(f"Cloud storage service not initialized")
        cloud_storage_service.download_file(
            object_name=request["object_name"],
            file_path=request["file_path"],
            bucket_name=request.get("bucket_name"),
        )
        return "Success"
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def cloud_storage_list_objects(request: Dict[str, Any]) -> List[str]:
    """List objects in a bucket with optional prefix filtering.

    Args:
        prefix: Optional. Only list objects beginning with this prefix. Defaults to "".
        bucket_name: Optional. Bucket to list from (defaults to instance default)

    Returns:
        List[str]: List of object names
    """
    try:
        cloud_storage_service = instantiate_cloud_storage()
        if not cloud_storage_service:
            raise RuntimeError(f"Cloud storage service not initialized")
        return cloud_storage_service.list_objects(
            prefix=request.get("prefix", ""), bucket_name=request.get("bucket_name")
        )
    except Exception as e:
        logger.error(f"Error listing objects: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def cloud_storage_delete_object(request: Dict[str, Any]) -> str:
    """Delete an object from cloud storage.

    Args:
        object_name: Required. Name of the object to delete
        bucket_name: Optional. Bucket to delete from (defaults to instance default)
    Returns:
        str: 'Success' if the object was deleted successfully
    """
    try:
        cloud_storage_service = instantiate_cloud_storage()
        if not cloud_storage_service:
            raise RuntimeError(f"Cloud storage service not initialized")
        cloud_storage_service.delete_object(
            object_name=request["object_name"], bucket_name=request.get("bucket_name")
        )
        return "Success"
    except Exception as e:
        logger.error(f"Error deleting object: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def cloud_storage_get_bucket_location(request: Dict[str, Any]) -> str:
    """Get the region where a bucket is located.

    Args:
        bucket_name: Optional. Name of the bucket. If None, uses default bucket.

    Returns:
        str: The region where the bucket is located
    """
    try:
        cloud_storage_service = instantiate_cloud_storage()
        if not cloud_storage_service:
            raise RuntimeError(f"Cloud storage service not initialized")
        return cloud_storage_service.get_bucket_location(
            bucket_name=request.get("bucket_name")
        )
    except Exception as e:
        logger.error(f"Error getting bucket location: {e}")
        raise handle_telnyx_error(e)
