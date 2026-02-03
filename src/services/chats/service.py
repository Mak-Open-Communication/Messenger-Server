"""Chat service for chat and member operations."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app import Application

from src.services.chats.repos import ChatsRepository, ChatMembersRepository
from src.services.users.repos import AccountsRepository
from src.models.api_models import Account, Chat, Result


class ChatService:
    """Service for chat operations."""

    def __init__(self, app: "Application"):
        """Initialize service with application."""

        self.app = app

        self.chats_repo = ChatsRepository(app)
        self.members_repo = ChatMembersRepository(app)

        self.accounts_repo = AccountsRepository(app)

    async def create_chat(
        self,
        owner_id: int,
        chat_name: str,
        member_usernames: list[str]
    ) -> Result[Chat]:
        """Create new chat with members."""

        # Resolve usernames to user IDs
        member_ids = [owner_id]
        for username in member_usernames:
            account = await self.accounts_repo.get_by_username(username)
            if not account:
                return Result(
                    success=False,
                    error=f"User '{username}' not found",
                    error_code="NOT_FOUND"
                )
            if account.id not in member_ids:
                member_ids.append(account.id)

        # Create chat
        chat_id = await self.chats_repo.create(owner_id, chat_name)

        # Add all members
        for user_id in member_ids:
            await self.members_repo.add_member(chat_id, user_id)

        return await self.get_chat_by_id(chat_id)

    async def get_chat_by_id(self, chat_id: int) -> Result[Chat]:
        """Get chat by ID with owner and members."""

        chat_db = await self.chats_repo.get_by_id(chat_id)
        if not chat_db:
            return Result(success=False, error="Chat not found", error_code="NOT_FOUND")

        # Get owner
        owner_db = await self.accounts_repo.get_by_id(chat_db.owner_user_id)
        owner = self.accounts_repo.to_api_model(owner_db, is_online=False)

        # Get members
        member_ids = await self.members_repo.get_member_user_ids(chat_id)
        members = []
        for user_id in member_ids:
            account_db = await self.accounts_repo.get_by_id(user_id)
            if account_db:
                # TODO: check is_online via NotifyManager
                members.append(self.accounts_repo.to_api_model(account_db, is_online=False))

        chat = Chat(
            chat_id=chat_db.id,
            chat_name=chat_db.chat_name,
            owner=owner,
            members=members,
            created_at=chat_db.created_at
        )

        return Result(success=True, data=chat)

    async def get_user_chats(self, user_id: int) -> Result[list[Chat]]:
        """Get all chats for user."""

        chats_db = await self.chats_repo.get_chats_by_user(user_id)

        chats = []
        for chat_db in chats_db:
            result = await self.get_chat_by_id(chat_db.id)
            if result.success:
                chats.append(result.data)

        return Result(success=True, data=chats)

    async def add_member(self, chat_id: int, username: str) -> Result[None]:
        """Add member to chat by username."""

        chat_db = await self.chats_repo.get_by_id(chat_id)
        if not chat_db:
            return Result(success=False, error="Chat not found", error_code="NOT_FOUND")

        account = await self.accounts_repo.get_by_username(username)
        if not account:
            return Result(success=False, error="User not found", error_code="NOT_FOUND")

        if await self.members_repo.is_member(chat_id, account.id):
            return Result(success=False, error="User already a member", error_code="VALIDATION_ERROR")

        await self.members_repo.add_member(chat_id, account.id)

        return Result(success=True, data=None)

    async def remove_member(self, chat_id: int, user_id: int) -> Result[None]:
        """Remove member from chat."""

        chat_db = await self.chats_repo.get_by_id(chat_id)
        if not chat_db:
            return Result(success=False, error="Chat not found", error_code="NOT_FOUND")

        if not await self.members_repo.is_member(chat_id, user_id):
            return Result(success=False, error="User is not a member", error_code="NOT_FOUND")

        await self.members_repo.remove_member(chat_id, user_id)

        return Result(success=True, data=None)

    async def leave_chat(self, chat_id: int, user_id: int) -> Result[None]:
        """User leaves chat."""

        return await self.remove_member(chat_id, user_id)

    async def rename_chat(self, chat_id: int, new_name: str) -> Result[None]:
        """Rename chat."""

        chat_db = await self.chats_repo.get_by_id(chat_id)
        if not chat_db:
            return Result(success=False, error="Chat not found", error_code="NOT_FOUND")

        await self.chats_repo.update_name(chat_id, new_name)

        return Result(success=True, data=None)

    async def delete_chat(self, chat_id: int) -> Result[None]:
        """Delete chat."""

        chat_db = await self.chats_repo.get_by_id(chat_id)
        if not chat_db:
            return Result(success=False, error="Chat not found", error_code="NOT_FOUND")

        await self.chats_repo.delete(chat_id)

        return Result(success=True, data=None)

    async def is_member(self, chat_id: int, user_id: int) -> bool:
        """Check if user is member of chat."""

        return await self.members_repo.is_member(chat_id, user_id)
