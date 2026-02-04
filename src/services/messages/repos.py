"""Message repositories for messages, contents, tags and files."""

import hashlib
import mimetypes
from dataclasses import dataclass
from uuid import uuid4

from src.common.base_repos import BaseDBRepository, BaseS3Repository
from src.models.db_models import MessageDB, MessageContentDB, MessageTagDB


@dataclass
class FileDownloadResult:
    """Result of file download with original filename."""

    data: bytes
    original_filename: str


class MessagesRepository(BaseDBRepository):
    """Repository for message operations."""

    repository_name = "messages"
    table_name = "messages"

    async def get_by_id(self, message_id: int) -> MessageDB | None:
        """Get message by ID."""

        row = await self.fetchrow(
            f"SELECT * FROM {self._get_table_name()} WHERE id = $1",
            message_id
        )

        return MessageDB(**row) if row else None

    async def create(self, chat_id: int, sender_id: int, is_read: bool = False, conn=None) -> int:
        """Create new message and return ID."""

        message_id = await self.fetchval(
            f"""INSERT INTO {self._get_table_name()} (chat_id, sender_user_id, is_read)
                VALUES ($1, $2, $3)
                RETURNING id""",
            chat_id, sender_id, is_read,
            conn=conn
        )

        return message_id

    async def mark_as_read(self, message_id: int, conn=None) -> bool:
        """Mark message as read."""

        result = await self.execute(
            f"UPDATE {self._get_table_name()} SET is_read = true WHERE id = $1",
            message_id,
            conn=conn
        )

        return "UPDATE" in result

    async def delete(self, message_id: int, conn=None) -> bool:
        """Delete message (CASCADE will delete contents and tags)."""

        result = await self.execute(
            f"DELETE FROM {self._get_table_name()} WHERE id = $1",
            message_id,
            conn=conn
        )

        return "DELETE" in result

    async def get_by_chat(
        self,
        chat_id: int,
        limit: int = 50,
        before_id: int | None = None
    ) -> list[MessageDB]:
        """Get messages from chat with cursor pagination."""

        if before_id:
            rows = await self.fetch(
                f"""SELECT * FROM {self._get_table_name()}
                    WHERE chat_id = $1 AND id < $2
                    ORDER BY id DESC
                    LIMIT $3""",
                chat_id, before_id, limit
            )
        else:
            rows = await self.fetch(
                f"""SELECT * FROM {self._get_table_name()}
                    WHERE chat_id = $1
                    ORDER BY id DESC
                    LIMIT $2""",
                chat_id, limit
            )

        return [MessageDB(**row) for row in rows]


class MessageContentsRepository(BaseDBRepository):
    """Repository for message content operations."""

    repository_name = "msg-contents"
    table_name = "msg_contents"

    async def add(
        self,
        message_id: int,
        resource_name: str,
        content_type: str,
        content: str,
        conn=None
    ) -> int:
        """Add content to message and return ID."""

        content_id = await self.fetchval(
            f"""INSERT INTO {self._get_table_name()} (message_id, resource_name, type, content)
                VALUES ($1, $2, $3, $4)
                RETURNING id""",
            message_id, resource_name, content_type, content,
            conn=conn
        )

        return content_id

    async def get_by_message(self, message_id: int) -> list[MessageContentDB]:
        """Get all contents for message."""

        rows = await self.fetch(
            f"SELECT * FROM {self._get_table_name()} WHERE message_id = $1",
            message_id
        )

        return [MessageContentDB(**row) for row in rows]

    async def delete_by_message(self, message_id: int, conn=None) -> bool:
        """Delete all contents for message."""

        result = await self.execute(
            f"DELETE FROM {self._get_table_name()} WHERE message_id = $1",
            message_id,
            conn=conn
        )

        return "DELETE" in result


class MessageTagsRepository(BaseDBRepository):
    """Repository for message tag operations."""

    repository_name = "msg-tags"
    table_name = "msg_tags"

    async def add(
        self,
        message_id: int,
        tag_type: str,
        tag_value: str,
        for_user_id: int | None = None,
        conn=None
    ) -> int:
        """Add tag to message and return ID."""

        tag_id = await self.fetchval(
            f"""INSERT INTO {self._get_table_name()} (message_id, type, tag, for_user_id)
                VALUES ($1, $2, $3, $4)
                RETURNING id""",
            message_id, tag_type, tag_value, for_user_id,
            conn=conn
        )

        return tag_id

    async def get_by_message(self, message_id: int) -> list[MessageTagDB]:
        """Get all tags for message."""

        rows = await self.fetch(
            f"SELECT * FROM {self._get_table_name()} WHERE message_id = $1",
            message_id
        )

        return [MessageTagDB(**row) for row in rows]

    async def delete_by_message(self, message_id: int, conn=None) -> bool:
        """Delete all tags for message."""

        result = await self.execute(
            f"DELETE FROM {self._get_table_name()} WHERE message_id = $1",
            message_id,
            conn=conn
        )

        return "DELETE" in result


class UsersFilesRepository(BaseS3Repository):
    """Repository for uploaded files in messages."""

    repository_name = "users-msg-files"
    resources_dir = "users/uploaded_files/"

    @staticmethod
    def _generate_s3_filename(original_filename: str, file_bytes: bytes) -> str:
        """
        Generate S3 filename: {name}_{md5}_{uuid}.{ext}

        Example: photo_a1b2c3d4_550e8400-e29b-41d4-a716-446655440000.jpg
        """

        # Split filename and extension
        if "." in original_filename:
            name_part, ext = original_filename.rsplit(".", 1)
            ext = f".{ext}"
        else:
            name_part = original_filename
            ext = ""

        # Generate MD5 hash of content
        content_hash = hashlib.md5(file_bytes).hexdigest()[:8]

        # Generate UUID
        unique_id = str(uuid4())

        return f"{name_part}_{content_hash}_{unique_id}{ext}"

    async def upload(
        self,
        chat_id: int,
        message_id: int,
        filename: str,
        file_bytes: bytes
    ) -> str:
        """Upload file to S3 and return S3 path."""

        s3_filename = self._generate_s3_filename(filename, file_bytes)
        s3_path = f"{chat_id}/{message_id}/{s3_filename}"
        full_key = self._get_full_key(s3_path)

        content_type, _ = mimetypes.guess_type(filename)
        metadata = {"original_filename": filename}

        await self.s3.upload_file(full_key, file_bytes, content_type=content_type, metadata=metadata)

        return s3_path

    async def download(self, s3_path: str) -> FileDownloadResult | None:
        """Download file from S3 with original filename."""

        full_key = self._get_full_key(s3_path)
        result = await self.s3.download_file_with_metadata(full_key)

        if result is None:
            return None

        data, metadata = result
        original_filename = metadata.get("original_filename", s3_path.split("/")[-1])

        return FileDownloadResult(data=data, original_filename=original_filename)

    async def delete(self, s3_path: str) -> bool:
        """Delete file from S3."""

        full_key = self._get_full_key(s3_path)
        return await self.s3.delete_file(full_key)

    async def get_url(self, s3_path: str, expires_in: int = 3600) -> str:
        """Get presigned URL for file."""

        full_key = self._get_full_key(s3_path)
        return await self.s3.get_file_url(full_key, expires_in=expires_in)
