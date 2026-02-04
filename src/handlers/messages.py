"""Messages transaction handlers."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app import Application

from src.middleware import logging_middleware, AuthMiddleware
from src.services.messages import MessageService, MessageContentInput
from src.services.chats import ChatService
from src.models.api_models import Result


def register_messages_handlers(app: "Application"):
    """Register messages handlers."""

    message_service = MessageService(app)
    chat_service = ChatService(app)
    auth = AuthMiddleware(app)

    @app.server.transaction(code="send_message")
    @logging_middleware.log_transaction
    @auth.require_auth
    async def send_message_trans(
        user_id: int,
        chat_id: int,
        contents: list[dict]
    ):
        """Send message to chat."""

        # Check if user is member
        if not await chat_service.is_member(chat_id, user_id):
            return Result(success=False, errors=[("FORBIDDEN", "Not a member of this chat")])

        # Convert dicts to MessageContentInput
        content_inputs = [
            MessageContentInput(
                type=c.get("type", "text"),
                resource_name=c.get("resource_name", "db"),
                content=c.get("content", "")
            )
            for c in contents
        ]

        result = await message_service.send_message(
            chat_id=chat_id,
            sender_id=user_id,
            contents=content_inputs
        )

        # Notify about new message
        if result.success and result.data:
            from src.services.users.repos import AccountsRepository
            accounts_repo = AccountsRepository(app)
            sender = await accounts_repo.get_by_id(user_id)

            chat_result = await chat_service.get_chat_by_id(chat_id)
            chat_name = chat_result.data.chat_name if chat_result.success else "Unknown"

            # Get message preview (first text content)
            message_preview = ""
            for content in result.data.contents:
                if hasattr(content, "text"):
                    message_preview = content.text
                    break

            await app.notify_man.send_new_message(
                chat_id=chat_id,
                sender_user_id=user_id,
                sender_username=sender.username if sender else "Unknown",
                chat_name=chat_name,
                message_id=result.data.message_id,
                message_preview=message_preview
            )

        return result

    @app.server.transaction(code="get_messages")
    @logging_middleware.log_transaction_debug
    @auth.require_auth
    async def get_messages_trans(
        user_id: int,
        chat_id: int,
        limit: int = 50,
        before_id: int | None = None
    ):
        """Get messages from chat with pagination."""

        # Check if user is member
        if not await chat_service.is_member(chat_id, user_id):
            return Result(success=False, errors=[("FORBIDDEN", "Not a member of this chat")])

        return await message_service.get_messages(
            chat_id=chat_id,
            limit=limit,
            before_id=before_id
        )

    @app.server.transaction(code="get_messages_hash")
    @logging_middleware.log_transaction_debug
    @auth.require_auth
    async def get_messages_hash_trans(
        user_id: int,
        chat_id: int,
        last_count: int = 40
    ):
        """Get MD5 hash of last N messages for sync check."""

        # Check if user is member
        if not await chat_service.is_member(chat_id, user_id):
            return Result(success=False, errors=[("FORBIDDEN", "Not a member of this chat")])

        return await message_service.get_messages_hash(
            chat_id=chat_id,
            last_count=last_count
        )

    @app.server.transaction(code="delete_message")
    @logging_middleware.log_transaction
    @auth.require_auth
    async def delete_message_trans(user_id: int, message_id: int):
        """Delete message (only own messages)."""

        # Get message to check chat membership and ownership
        msg_result = await message_service.get_message_by_id(message_id)
        if not msg_result.success:
            return msg_result

        chat_id = msg_result.data.chat_id

        result = await message_service.delete_message(
            message_id=message_id,
            user_id=user_id
        )

        # Notify about message deletion
        if result.success:
            await app.notify_man.send_message_deleted(
                chat_id=chat_id,
                message_id=message_id,
                deleter_user_id=user_id
            )

        return result

    @app.server.transaction(code="edit_message")
    @logging_middleware.log_transaction
    @auth.require_auth
    async def edit_message_trans(
        user_id: int,
        message_id: int,
        new_contents: list[dict]
    ):
        """Edit message (only own messages)."""

        # Convert dicts to MessageContentInput
        content_inputs = [
            MessageContentInput(
                type=c.get("type", "text"),
                resource_name=c.get("resource_name", "db"),
                content=c.get("content", "")
            )
            for c in new_contents
        ]

        result = await message_service.edit_message(
            message_id=message_id,
            user_id=user_id,
            new_contents=content_inputs
        )

        # Notify about message edit
        if result.success and result.data:
            await app.notify_man.send_message_edited(
                chat_id=result.data.chat_id,
                message_id=message_id,
                editor_user_id=user_id
            )

        return result

    @app.server.transaction(code="mark_read")
    @logging_middleware.log_transaction_debug
    @auth.require_auth
    async def mark_read_trans(user_id: int, message_id: int):
        """Mark message as read."""

        # Get message to check chat membership
        msg_result = await message_service.get_message_by_id(message_id)
        if not msg_result.success:
            return msg_result

        chat_id = msg_result.data.chat_id

        # Check if user is member
        if not await chat_service.is_member(chat_id, user_id):
            return Result(success=False, errors=[("FORBIDDEN", "Not a member of this chat")])

        result = await message_service.mark_read(message_id=message_id)

        # Notify about read status
        if result.success:
            await app.notify_man.send_read_status(
                chat_id=chat_id,
                message_id=message_id,
                reader_user_id=user_id
            )

        return result

    @app.server.transaction(code="send_typing")
    @logging_middleware.log_transaction_debug
    @auth.require_auth
    async def send_typing_trans(user_id: int, chat_id: int):
        """Send typing indicator to chat."""

        # Check if user is member
        if not await chat_service.is_member(chat_id, user_id):
            return Result(success=False, errors=[("FORBIDDEN", "Not a member of this chat")])

        await app.notify_man.send_typing(chat_id=chat_id, user_id=user_id)

        return Result(success=True, errors=[], data=None)
