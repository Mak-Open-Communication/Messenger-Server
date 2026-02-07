"""Message service for message operations."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app import Application

from src.services.messages.repos import (
    MessagesRepository,
    MessageContentsRepository,
    MessageTagsRepository,
    UsersFilesRepository
)
from src.services.users.repos import AccountsRepository

from src.models.api_models import (
    Message,
    MessageTag,
    MsgContentTextChunk,
    MsgContentFile,
    Result
)


@dataclass
class MessageContentInput:
    """Input for message content."""

    type: str  # "text" or "file"
    resource_name: str  # "db" or "s3"
    content: str | bytes


class MessageService:
    """Service for message operations."""

    def __init__(self, app: "Application"):
        """Initialize service with application."""

        self.app = app

        self.messages_repo = MessagesRepository(app)
        self.contents_repo = MessageContentsRepository(app)
        self.tags_repo = MessageTagsRepository(app)

        self.files_repo = UsersFilesRepository(app)

        self.accounts_repo = AccountsRepository(app)

    async def send_message(
        self,
        chat_id: int,
        sender_id: int,
        contents: list[MessageContentInput]
    ) -> Result[Message]:
        """Send message with contents."""

        if not contents:
            return Result(success=False, errors=[("VALIDATION_ERROR", "Message must have content")])

        # Create message
        message_id = await self.messages_repo.create(chat_id, sender_id)

        # Add contents
        for content_input in contents:
            if content_input.type == "text":
                # Text content - split into chunks if needed
                text = content_input.content if isinstance(content_input.content, str) else content_input.content.decode()
                chunks = [text[i:i+2048] for i in range(0, len(text), 2048)]

                for chunk in chunks:
                    await self.contents_repo.add(
                        message_id=message_id,
                        resource_name="db",
                        content_type="text",
                        content=chunk
                    )

            elif content_input.type == "file":
                # File content - upload to S3
                file_bytes = content_input.content if isinstance(content_input.content, bytes) else content_input.content.encode()
                filename = content_input.resource_name

                s3_path = await self.files_repo.upload(chat_id, message_id, filename, file_bytes)

                await self.contents_repo.add(
                    message_id=message_id,
                    resource_name="s3",
                    content_type="file",
                    content=s3_path
                )

        return await self.get_message_by_id(message_id)

    async def get_message_by_id(self, message_id: int) -> Result[Message]:
        """Get message by ID with sender, contents and tags."""

        message_db = await self.messages_repo.get_by_id(message_id)
        if not message_db:
            return Result(success=False, errors=[("NOT_FOUND", "Message not found")])

        # Get sender
        sender_db = await self.accounts_repo.get_by_id(message_db.sender_user_id)
        sender = self.accounts_repo.to_api_model(sender_db, is_online=self.app.notify_man.is_online(sender_db.id))

        # Get contents
        contents_db = await self.contents_repo.get_by_message(message_id)
        contents = []
        for content_db in contents_db:
            if content_db.type == "text":
                contents.append(MsgContentTextChunk(text=content_db.content))
            elif content_db.type == "file":
                # Download file from S3
                file_result = await self.files_repo.download(content_db.content)
                if file_result:
                    contents.append(MsgContentFile(filename=file_result.original_filename, payload=file_result.data))
                else:
                    contents.append(MsgContentFile(filename="unknown", payload=b""))

        # Get tags
        tags_db = await self.tags_repo.get_by_message(message_id)
        tags = []
        for tag_db in tags_db:
            for_user = None
            if tag_db.for_user_id:
                for_user_db = await self.accounts_repo.get_by_id(tag_db.for_user_id)
                if for_user_db:
                    for_user = self.accounts_repo.to_api_model(
                        for_user_db,
                        is_online=self.app.notify_man.is_online(for_user_db.id)
                    )

            tags.append(MessageTag(
                tag_id=tag_db.id,
                message_id=tag_db.message_id,
                for_user=for_user,
                type=tag_db.type,
                tag=tag_db.tag
            ))

        message = Message(
            message_id=message_db.id,
            chat_id=message_db.chat_id,
            sender_user=sender,
            is_read=message_db.is_read,
            tags=tags,
            contents=contents,
            created_at=message_db.created_at.isoformat()
        )

        return Result(success=True, errors=[], data=message)

    async def get_messages(
        self,
        chat_id: int,
        limit: int = 50,
        before_id: int | None = None
    ) -> Result[list[Message]]:
        """Get messages from chat with pagination."""

        messages_db = await self.messages_repo.get_by_chat(chat_id, limit, before_id)

        messages = []
        for message_db in messages_db:
            result = await self.get_message_by_id(message_db.id)
            if result.success:
                messages.append(result.data)

        return Result(success=True, errors=[], data=messages)

    async def delete_message(self, message_id: int, user_id: int) -> Result[None]:
        """Delete message (only by author)."""

        message_db = await self.messages_repo.get_by_id(message_id)
        if not message_db:
            return Result(success=False, errors=[("NOT_FOUND", "Message not found")])

        if message_db.sender_user_id != user_id:
            return Result(success=False, errors=[("FORBIDDEN", "Can only delete own messages")])

        # Delete files from S3
        contents_db = await self.contents_repo.get_by_message(message_id)
        for content_db in contents_db:
            if content_db.resource_name == "s3":
                await self.files_repo.delete(content_db.content)

        # Delete message (CASCADE will delete contents and tags)
        await self.messages_repo.delete(message_id)

        return Result(success=True, errors=[], data=None)

    async def edit_message(
        self,
        message_id: int,
        user_id: int,
        new_contents: list[MessageContentInput]
    ) -> Result[Message]:
        """Edit message contents (only by author)."""

        message_db = await self.messages_repo.get_by_id(message_id)
        if not message_db:
            return Result(success=False, errors=[("NOT_FOUND", "Message not found")])

        if message_db.sender_user_id != user_id:
            return Result(success=False, errors=[("FORBIDDEN", "Can only edit own messages")])

        # Delete old files from S3
        contents_db = await self.contents_repo.get_by_message(message_id)
        for content_db in contents_db:
            if content_db.resource_name == "s3":
                await self.files_repo.delete(content_db.content)

        # Delete old contents
        await self.contents_repo.delete_by_message(message_id)

        # Add new contents
        for content_input in new_contents:
            if content_input.type == "text":
                text = content_input.content if isinstance(content_input.content, str) else content_input.content.decode()
                chunks = [text[i:i+2048] for i in range(0, len(text), 2048)]

                for chunk in chunks:
                    await self.contents_repo.add(
                        message_id=message_id,
                        resource_name="db",
                        content_type="text",
                        content=chunk
                    )

            elif content_input.type == "file":
                file_bytes = content_input.content if isinstance(content_input.content, bytes) else content_input.content.encode()
                filename = content_input.resource_name

                s3_path = await self.files_repo.upload(message_db.chat_id, message_id, filename, file_bytes)

                await self.contents_repo.add(
                    message_id=message_id,
                    resource_name="s3",
                    content_type="file",
                    content=s3_path
                )

        return await self.get_message_by_id(message_id)

    async def mark_read(self, message_id: int) -> Result[None]:
        """Mark message as read."""

        message_db = await self.messages_repo.get_by_id(message_id)
        if not message_db:
            return Result(success=False, errors=[("NOT_FOUND", "Message not found")])

        await self.messages_repo.mark_as_read(message_id)

        return Result(success=True, errors=[], data=None)

    async def get_messages_hash(self, chat_id: int, last_count: int = 40) -> Result[str]:
        """
        Get MD5 hash of last N messages for sync check.

        Hash is calculated from JSON of messages (message_id + content).
        Messages are ordered from newest to oldest.
        """

        import hashlib
        import json

        messages_db = await self.messages_repo.get_by_chat(chat_id, limit=last_count)

        # Build data for hashing: list of {message_id, contents}
        hash_data = []
        for message_db in messages_db:
            contents_db = await self.contents_repo.get_by_message(message_db.id)

            # Collect all content strings (text or s3 path)
            content_strings = [c.content for c in contents_db]

            hash_data.append({
                "message_id": message_db.id,
                "content": content_strings
            })

        # Serialize to JSON and hash
        json_str = json.dumps(hash_data, ensure_ascii=False, sort_keys=True)
        hash_result = hashlib.md5(json_str.encode()).hexdigest()

        return Result(success=True, errors=[], data=hash_result)
