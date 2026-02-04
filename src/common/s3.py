"""
S3 API module for object storage operations.
"""

import aioboto3
import logging

from typing import Optional
from contextlib import asynccontextmanager
from botocore.exceptions import ClientError

from src.config import settings


class S3API:
    """S3 object storage API."""

    def __init__(self):
        """Initialize S3 API."""

        self.logger = logging.getLogger("s3-api")
        self.logger.setLevel(settings.logging_level)

        self.session: Optional[aioboto3.Session] = None
        self.endpoint_url = settings.s3_endpoint_url
        self.bucket_name = settings.s3_bucket_name

    def connect(self) -> None:
        """Initialize S3 session."""

        self.session = aioboto3.Session(
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
        )

    async def safely_connect(self) -> None:
        """Safely connect to S3."""

        self.connect()
        s3_status = await self.ping()

        if s3_status:
            self.logger.info("S3 connected successfully")
        else:
            self.logger.critical(
                "S3 connection failed, make sure that correct access keys are used and that server is accessible.")

            raise RuntimeError(
                "S3 connection failed, make sure that correct access keys are used and that server is accessible.")

    async def disconnect(self) -> None:
        """Close S3 session (cleanup if needed)."""

        self.session = None

    @asynccontextmanager
    async def _client(self):
        """Get S3 client context manager."""
        async with self.session.client(
            service_name="s3",
            endpoint_url=self.endpoint_url,
            verify=settings.s3_verify_ssl,
        ) as client:
            yield client

    async def ping(self) -> bool:
        """
        Check S3 connectivity by listing buckets.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            async with self._client() as client:
                await client.head_bucket(Bucket=self.bucket_name)
            return True
        except Exception:
            return False

    async def upload_file(
        self,
        key: str,
        data: bytes,
        content_type: Optional[str] = None,
    ) -> bool:
        """
        Upload file to S3.

        Args:
            key: Object key (path in bucket)
            data: File data as bytes
            content_type: MIME type (e.g., 'image/png')

        Returns:
            True if successful
        """
        try:
            async with self._client() as client:
                extra_args = {}
                if content_type:
                    extra_args["ContentType"] = content_type

                await client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=data,
                    **extra_args,
                )
            return True
        except ClientError:
            return False

    async def download_file(self, key: str) -> Optional[bytes]:
        """
        Download file from S3.

        Args:
            key: Object key (path in bucket)

        Returns:
            File data as bytes or None if not found
        """
        try:
            async with self._client() as client:
                response = await client.get_object(
                    Bucket=self.bucket_name,
                    Key=key,
                )
                async with response["Body"] as stream:
                    return await stream.read()
        except ClientError:
            return None

    async def delete_file(self, key: str) -> bool:
        """
        Delete file from S3.

        Args:
            key: Object key (path in bucket)

        Returns:
            True if successful
        """
        try:
            async with self._client() as client:
                await client.delete_object(
                    Bucket=self.bucket_name,
                    Key=key,
                )
            return True
        except ClientError:
            return False

    async def file_exists(self, key: str) -> bool:
        """
        Check if file exists in S3.

        Args:
            key: Object key (path in bucket)

        Returns:
            True if file exists
        """
        try:
            async with self._client() as client:
                await client.head_object(
                    Bucket=self.bucket_name,
                    Key=key,
                )
            return True
        except ClientError:
            return False

    async def get_file_url(self, key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generate presigned URL for file download.

        Args:
            key: Object key (path in bucket)
            expires_in: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned URL or None if error
        """
        try:
            async with self._client() as client:
                url = await client.generate_presigned_url(
                    "get_object",
                    Params={
                        "Bucket": self.bucket_name,
                        "Key": key,
                    },
                    ExpiresIn=expires_in,
                )
            return url
        except ClientError:
            return None

    async def list_files(self, prefix: str = "") -> list[str]:
        """
        List files in bucket with optional prefix.

        Args:
            prefix: Filter by prefix (e.g., 'images/')

        Returns:
            List of object keys
        """
        try:
            async with self._client() as client:
                response = await client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix,
                )
                if "Contents" in response:
                    return [obj["Key"] for obj in response["Contents"]]
                return []
        except ClientError:
            return []
