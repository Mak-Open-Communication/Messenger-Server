"""Chats transaction handlers."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app import Application

from src.middleware import logging_middleware, AuthMiddleware
from src.services.chats import ChatService
from src.models.api_models import Result


def register_chats_handlers(app: "Application"):
    """Register chats handlers."""

    chat_service = ChatService(app)
    auth = AuthMiddleware(app)

    @app.server.transaction(code="create_chat")
    @logging_middleware.log_transaction
    @auth.require_auth
    async def create_chat_trans(user_id: int, chat_name: str, members: list[str]):
        """Create new chat with members."""

        result = await chat_service.create_chat(
            owner_id=user_id,
            chat_name=chat_name,
            member_usernames=members
        )

        # Notify about chat creation
        if result.success and result.data:
            await app.notify_man.send_chat_created(
                chat_id=result.data.chat_id,
                chat_name=result.data.chat_name,
                creator_user_id=user_id
            )

        return result

    @app.server.transaction(code="get_chat_info")
    @logging_middleware.log_transaction_debug
    @auth.require_auth
    async def get_chat_info_trans(user_id: int, chat_id: int):
        """Get chat info by ID."""

        # Check if user is member
        if not await chat_service.is_member(chat_id, user_id):
            return Result(success=False, errors=[("FORBIDDEN", "Not a member of this chat")])

        return await chat_service.get_chat_by_id(chat_id=chat_id)

    @app.server.transaction(code="get_my_chats")
    @logging_middleware.log_transaction_debug
    @auth.require_auth
    async def get_my_chats_trans(user_id: int):
        """Get all chats for current user."""

        return await chat_service.get_user_chats(user_id=user_id)

    @app.server.transaction(code="add_member")
    @logging_middleware.log_transaction
    @auth.require_auth
    async def add_member_trans(user_id: int, chat_id: int, username: str):
        """Add member to chat by username."""

        # Check if user is member
        if not await chat_service.is_member(chat_id, user_id):
            return Result(success=False, errors=[("FORBIDDEN", "Not a member of this chat")])

        result = await chat_service.add_member(chat_id=chat_id, username=username)

        # Notify about member addition
        if result.success:
            # Get added user ID
            from src.services.users.repos import AccountsRepository
            accounts_repo = AccountsRepository(app)
            added_user = await accounts_repo.get_by_username(username)
            if added_user:
                await app.notify_man.send_member_added(
                    chat_id=chat_id,
                    added_user_id=added_user.id,
                    adder_user_id=user_id
                )

        return result

    @app.server.transaction(code="remove_member")
    @logging_middleware.log_transaction
    @auth.require_auth
    async def remove_member_trans(user_id: int, chat_id: int, target_user_id: int):
        """Remove member from chat."""

        # Check if user is member
        if not await chat_service.is_member(chat_id, user_id):
            return Result(success=False, errors=[("FORBIDDEN", "Not a member of this chat")])

        result = await chat_service.remove_member(chat_id=chat_id, user_id=target_user_id)

        # Notify about member removal
        if result.success:
            await app.notify_man.send_member_removed(
                chat_id=chat_id,
                removed_user_id=target_user_id,
                remover_user_id=user_id
            )

        return result

    @app.server.transaction(code="rename_chat")
    @logging_middleware.log_transaction
    @auth.require_auth
    async def rename_chat_trans(user_id: int, chat_id: int, new_name: str):
        """Rename chat."""

        # Check if user is member
        if not await chat_service.is_member(chat_id, user_id):
            return Result(success=False, errors=[("FORBIDDEN", "Not a member of this chat")])

        return await chat_service.rename_chat(chat_id=chat_id, new_name=new_name)

    @app.server.transaction(code="leave_chat")
    @logging_middleware.log_transaction
    @auth.require_auth
    async def leave_chat_trans(user_id: int, chat_id: int):
        """Leave chat."""

        # Check if user is member
        if not await chat_service.is_member(chat_id, user_id):
            return Result(success=False, errors=[("FORBIDDEN", "Not a member of this chat")])

        result = await chat_service.leave_chat(chat_id=chat_id, user_id=user_id)

        # Notify about member leaving
        if result.success:
            await app.notify_man.send_member_removed(
                chat_id=chat_id,
                removed_user_id=user_id,
                remover_user_id=user_id
            )

        return result

    @app.server.transaction(code="delete_chat")
    @logging_middleware.log_transaction
    @auth.require_auth
    async def delete_chat_trans(user_id: int, chat_id: int):
        """Delete chat."""

        # Check if user is member
        if not await chat_service.is_member(chat_id, user_id):
            return Result(success=False, errors=[("FORBIDDEN", "Not a member of this chat")])

        return await chat_service.delete_chat(chat_id=chat_id)
