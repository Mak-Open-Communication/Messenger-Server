"""Messages, msg contents, tags & uploaded files repositories"""

import mimetypes

from typing import Optional, List

from src.common.base_repos import BaseDBRepository, BaseS3Repository

from src.models.db_models import MessageDB, MessageContentDB, MessageTagDB


class UsersFilesRepository(BaseS3Repository):
    """Uploaded files repository (on messages)"""

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


class MessagesRepository(BaseDBRepository):
    """Repository for message operations"""

    repository_name = "messages"
    table_name = "messages"

    async def get_by_id(self, message_id: int) -> Optional[MessageDB]:
        """Get message by ID"""

        row = await self.fetchrow(
            f"SELECT * FROM {self._get_table_name()} WHERE id = $1",
            message_id
        )

        return MessageDB(**row) if row else None

    async def create(self, chat_id: int, sender_id: int, is_read: bool = False, conn=None) -> int:
        """Create new message and return ID"""

        message_id = await self.fetchval(
            f"""INSERT INTO {self._get_table_name()} (chat_id, sender, is_read)
                VALUES ($1, $2, $3)
                RETURNING id""",
            chat_id, sender_id, is_read,
            conn=conn
        )

        return message_id

    async def mark_as_read(self, message_id: int, conn=None) -> bool:
        """Mark message as read"""

        result = await self.execute(
            f"UPDATE {self._get_table_name()} SET is_read = true WHERE id = $1",
            message_id,
            conn=conn
        )

        return "UPDATE" in result

    async def delete(self, message_id: int, conn=None) -> bool:
        """Delete message (CASCADE will delete contents and tags)"""

        result = await self.execute(
            f"DELETE FROM {self._get_table_name()} WHERE id = $1",
            message_id,
            conn=conn
        )

        return "DELETE" in result

    async def get_by_chat(self, chat_id: int, limit: int = 50, offset: int = 0) -> List[MessageDB]:
        """Get messages from chat with pagination"""

        rows = await self.fetch(
            f"""SELECT * FROM {self._get_table_name()}
                WHERE chat_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3""",
            chat_id, limit, offset
        )

        return [MessageDB(**row) for row in rows]


class MessageContentsRepository(BaseDBRepository):
    """Repository for message content operations"""

    repository_name = "msg-contents"
    table_name = "msg_contents"

    async def add(self, message_id: int, content_type: str, content: str, resource_name: str = "", conn=None) -> int:
        """Add content to message and return ID"""

        content_id = await self.fetchval(
            f"""INSERT INTO {self._get_table_name()} (message_id, type, content, resource_name)
                VALUES ($1, $2, $3, $4)
                RETURNING id""",
            message_id, content_type, content, resource_name,
            conn=conn
        )

        return content_id

    async def get_by_message(self, message_id: int) -> List[MessageContentDB]:
        """Get all contents for message"""

        rows = await self.fetch(
            f"SELECT * FROM {self._get_table_name()} WHERE message_id = $1",
            message_id
        )

        return [MessageContentDB(**row) for row in rows]

    async def update_text_content(
        self,
        message_id: int,
        new_text: str,
        conn=None
    ) -> bool:
        """Update text content of message"""

        result = await self.execute(
            f"UPDATE {self._get_table_name()} SET content = $1 WHERE message_id = $2 AND type = 'Text'",
            new_text, message_id,
            conn=conn
        )

        return "UPDATE" in result

    async def delete_by_message(self, message_id: int, conn=None) -> bool:
        """Delete all contents for message"""

        result = await self.execute(
            f"DELETE FROM {self._get_table_name()} WHERE message_id = $1",
            message_id,
            conn=conn
        )

        return "DELETE" in result


class MessageTagsRepository(BaseDBRepository):
    """Repository for message tag operations"""

    repository_name = "msg-tags"
    table_name = "msg_tags"

    async def add(
        self,
        message_id: int,
        tag_type: str,
        tag_value: str = "",
        conn=None
    ) -> int:
        """Add tag to message and return ID"""

        tag_id = await self.fetchval(
            f"""INSERT INTO {self._get_table_name()} (message_id, type, tag)
                VALUES ($1, $2, $3)
                RETURNING id""",
            message_id, tag_type, tag_value,
            conn=conn
        )

        return tag_id

    async def get_by_message(self, message_id: int) -> List[MessageTagDB]:
        """Get all tags for message"""

        rows = await self.fetch(
            f"SELECT * FROM {self._get_table_name()} WHERE message_id = $1",
            message_id
        )

        return [MessageTagDB(**row) for row in rows]

    async def delete_by_message(self, message_id: int, conn=None) -> bool:
        """Delete all tags for message"""

        result = await self.execute(
            f"DELETE FROM {self._get_table_name()} WHERE message_id = $1",
            message_id,
            conn=conn
        )

        return "DELETE" in result
