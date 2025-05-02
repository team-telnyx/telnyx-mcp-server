import os
from functools import lru_cache
from typing import Dict, List, Optional, TypedDict

import boto3
from botocore.client import Config


class BucketInfo(TypedDict):
    """Type definition for bucket information"""

    name: str
    region: str


class CloudStorageService:
    """Service for interacting with Telnyx Cloud Storage (S3-compatible)"""

    VALID_REGIONS = ["us-west-1", "us-central-1", "us-east-1"]

    def __init__(
        self,
        access_key_id: str,
        secret_access_key: str,
        default_region: str = "us-east-1",
        bucket_name: Optional[str] = None,
    ):
        """Initialize the cloud storage service.

        Args:
            access_key_id: AWS access key ID
            secret_access_key: AWS secret access key
            default_region: Default region to use when bucket location is unknown
            bucket_name: Default bucket name to use for operations

        Raises:
            ValueError: If an invalid region is provided
        """
        if default_region not in self.VALID_REGIONS:
            raise ValueError(
                f"Invalid region. Must be one of: {', '.join(self.VALID_REGIONS)}"
            )

        # Create S3 clients for each region
        self.s3_clients: Dict[str, boto3.client] = {}
        for region in self.VALID_REGIONS:
            endpoint_url = f"https://{region}.telnyxcloudstorage.com"
            self.s3_clients[region] = boto3.client(
                "s3",
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                endpoint_url=endpoint_url,
                region_name=region,
                config=Config(signature_version="s3v4"),
            )

        self.default_region = default_region
        self.default_bucket_name = bucket_name
        self._bucket_region_cache: Dict[str, str] = {}

    def list_buckets(self) -> List[BucketInfo]:
        """List all buckets across all regions.

        Returns:
            List[BucketInfo]: List of dictionaries containing bucket information:
                - name: Name of the bucket
                - region: Region where the bucket is located

        Note:
            This method may take some time as it needs to:
            1. List buckets from each region
            2. Get the location of each bucket
            3. Deduplicate the results
        """
        seen_buckets = set()
        buckets: List[BucketInfo] = []

        # Try listing buckets from each region
        for region in self.VALID_REGIONS:
            try:
                response = self.s3_clients[region].list_buckets()
                for bucket in response.get("Buckets", []):
                    bucket_name = bucket["Name"]

                    # Skip if we've already processed this bucket
                    if bucket_name in seen_buckets:
                        continue

                    try:
                        # Get the actual region for this bucket
                        bucket_region = self._get_bucket_region(bucket_name)
                        buckets.append({"name": bucket_name, "region": bucket_region})
                        seen_buckets.add(bucket_name)
                    except ValueError:
                        # Skip buckets whose region we can't determine
                        continue

            except Exception:
                # If listing fails in this region, continue to the next
                continue

        return buckets

    def _get_bucket_name(self, bucket_name: Optional[str] = None) -> str:
        """Get the bucket name to use for an operation.

        Args:
            bucket_name: Name of the bucket. If None, uses default bucket.

        Returns:
            str: The bucket name to use

        Raises:
            ValueError: If no bucket name is provided or set as default
        """
        bucket_name = bucket_name or self.default_bucket_name
        if not bucket_name:
            raise ValueError(
                "Bucket name must be provided either during initialization or method call"
            )
        return bucket_name

    @lru_cache(maxsize=100)
    def _get_bucket_region(self, bucket_name: str) -> str:
        """Get the region where a bucket is located (with caching).

        Args:
            bucket_name: Name of the bucket

        Returns:
            str: The region where the bucket is located

        Raises:
            ValueError: If the bucket's region cannot be determined
        """
        # Try to get location from default region first
        try:
            response = self.s3_clients[self.default_region].get_bucket_location(
                Bucket=bucket_name
            )
            location = response.get("LocationConstraint") or "us-east-1"
            if location in self.VALID_REGIONS:
                return location
        except Exception:
            pass

        # If that fails, try each region until we find it
        for region in self.VALID_REGIONS:
            if region == self.default_region:
                continue
            try:
                response = self.s3_clients[region].get_bucket_location(
                    Bucket=bucket_name
                )
                location = response.get("LocationConstraint") or "us-east-1"
                if location in self.VALID_REGIONS:
                    return location
            except Exception:
                continue

        raise ValueError(f"Could not determine region for bucket: {bucket_name}")

    def _get_client_for_bucket(self, bucket_name: str) -> boto3.client:
        """Get the appropriate S3 client for the given bucket.

        Args:
            bucket_name: Name of the bucket

        Returns:
            boto3.client: The S3 client for the bucket's region
        """
        region = self._get_bucket_region(bucket_name)
        return self.s3_clients[region]

    def upload_file(
        self,
        file_path: str,
        object_name: Optional[str] = None,
        bucket_name: Optional[str] = None,
    ):
        """Upload a file to cloud storage.

        Args:
            file_path: **ABSOLUTE PATH** to the file to upload
            object_name: Name to give the object in storage (defaults to file name)
            bucket_name: Bucket to upload to (defaults to instance default)

        Returns:
            str: `Success!!` if it uploaded, otherwise returns an exception message
        """
        if not object_name:
            object_name = os.path.basename(file_path)

        bucket = self._get_bucket_name(bucket_name)
        s3 = self._get_client_for_bucket(bucket)
        try:
            s3.upload_file(file_path, bucket, object_name)
            return "Success!!"
        except Exception as e:
            return f"An error occurred: {e}"

    def create_bucket(self, bucket_name: str, region: str) -> str:
        """Create a new bucket.

        Args:
            bucket_name: Name of the bucket to create
            region: Region to create the bucket in
        Returns:
            str: `Success!!` if it uploaded, otherwise returns an exception message
        """
        region = region or self.default_region
        s3 = self.s3_clients[region]
        try:
            s3.create_bucket(
                Bucket=bucket_name, CreateBucketConfiguration={"LocationConstraint": region}
            )
            return "Success!!"
        except Exception as e:
            return f"An error occurred: {e}"

    def download_file(
        self, object_name: str, file_path: str, bucket_name: Optional[str] = None
    ) -> None:
        """Download a file from cloud storage.

        Args:
            object_name: Name of the object to download
            file_path: Path where to save the downloaded file
            bucket_name: Bucket to download from (defaults to instance default)
        """
        bucket = self._get_bucket_name(bucket_name)
        s3 = self._get_client_for_bucket(bucket)
        s3.download_file(bucket, object_name, file_path)

    def list_objects(
        self, prefix: str = "", bucket_name: Optional[str] = None
    ) -> List[str]:
        """List objects in a bucket with optional prefix filtering.

        Args:
            prefix: Only list objects beginning with this prefix
            bucket_name: Bucket to list from (defaults to instance default)

        Returns:
            List[str]: List of object names
        """
        bucket = self._get_bucket_name(bucket_name)
        s3 = self._get_client_for_bucket(bucket)
        paginator = s3.get_paginator("list_objects_v2")

        object_names = []
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            if "Contents" in page:
                object_names.extend(obj["Key"] for obj in page["Contents"])

        return object_names

    def delete_object(
        self, object_name: str, bucket_name: Optional[str] = None
    ) -> None:
        """Delete an object from cloud storage.

        Args:
            object_name: Name of the object to delete
            bucket_name: Bucket to delete from (defaults to instance default)
        """
        bucket = self._get_bucket_name(bucket_name)
        s3 = self._get_client_for_bucket(bucket)
        s3.delete_object(Bucket=bucket, Key=object_name)

    def get_bucket_location(self, bucket_name: Optional[str] = None) -> str:
        """Get the region where a bucket is located.

        Args:
            bucket_name: Name of the bucket. If None, uses default bucket.

        Returns:
            str: The region where the bucket is located
        """
        bucket = self._get_bucket_name(bucket_name)
        return self._get_bucket_region(bucket)
