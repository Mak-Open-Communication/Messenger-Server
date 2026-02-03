"""Media storage repositories"""

import mimetypes

from typing import Optional

from src.common.base_repos import BaseS3Repository


class UsersFilesRepository(BaseS3Repository):
    """Repository for user message files in S3"""

    repository_name = "users-msg-files"
    resources_dir = "users/uploaded_files/"

    async def upload(
        self,
        chat_id: int,
        message_id: int,
        filename: str,
        file_bytes: bytes
    ) -> tuple[str, str]:
        """Upload file to S3 and return resource_name and URL"""

        resource_name = f"{chat_id}/{message_id}/{filename}"
        full_key = self._get_full_key(resource_name)

        # Guess content type
        content_type, _ = mimetypes.guess_type(filename)

        # Upload to S3
        await self.s3.upload_file(full_key, file_bytes, content_type=content_type)

        # Generate presigned URL
        url = await self.s3.get_file_url(full_key, expires_in=3600)

        return resource_name, url

    async def download(self, resource_name: str) -> Optional[bytes]:
        """Download file from S3 by resource_name"""

        full_key = self._get_full_key(resource_name)
        return await self.s3.download_file(full_key)

    async def delete(self, resource_name: str) -> bool:
        """Delete file from S3"""

        full_key = self._get_full_key(resource_name)
        return await self.s3.delete_file(full_key)

    async def exists(self, resource_name: str) -> bool:
        """Check if file exists in S3"""

        full_key = self._get_full_key(resource_name)
        return await self.s3.file_exists(full_key)


class AvatarsRepository(BaseS3Repository):
    """Repository for user avatars (future implementation)"""

    repository_name = "avatars"
    resources_dir = "users/avatars/"

    # TODO: Implement when avatars are needed
