"""Chat service with chat and member repositories"""

from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.app import Application

from src.services.resources_service import BaseDBRepository
from src.models.db_models import ChatDB, ChatMemberDB


class ChatRepository(BaseDBRepository):
    """Repository for chat operations"""

    repository_name = "chats"
    table_name = "chats"

    async def get_by_id(self, chat_id: int) -> Optional[ChatDB]:
        """Get chat by ID"""

        row = await self.fetchrow(
            f"SELECT * FROM {self._get_table_name()} WHERE id = $1",
            chat_id
        )

        return ChatDB(**row) if row else None

    async def create(self, owner_id: int, name: str, conn=None) -> int:
        """Create new chat and return ID"""

        chat_id = await self.fetchval(
            f"""INSERT INTO {self._get_table_name()} (owner, name)
                VALUES ($1, $2)
                RETURNING id""",
            owner_id, name,
            conn=conn
        )

        return chat_id

    async def update_name(self, chat_id: int, name: str, conn=None) -> bool:
        """Update chat name"""

        result = await self.execute(
            f"UPDATE {self._get_table_name()} SET name = $1 WHERE id = $2",
            name, chat_id,
            conn=conn
        )

        return "UPDATE" in result

    async def delete(self, chat_id: int, conn=None) -> bool:
        """Delete chat (CASCADE will delete members and messages)"""

        result = await self.execute(
            f"DELETE FROM {self._get_table_name()} WHERE id = $1",
            chat_id,
            conn=conn
        )

        return "DELETE" in result

    async def get_chats_by_user(self, user_id: int) -> List[ChatDB]:
        """Get all chats where user is member"""

        rows = await self.fetch(
            f"""SELECT c.* FROM {self._get_table_name()} c
                JOIN {self.schema_name}.chat_members cm ON c.id = cm.chat_id
                WHERE cm.user_id = $1
                ORDER BY c.created_at DESC""",
            user_id
        )

        return [ChatDB(**row) for row in rows]


class ChatMemberRepository(BaseDBRepository):
    """Repository for chat member operations"""

    repository_name = "chat-members"
    table_name = "chat_members"

    async def add_member(self, chat_id: int, user_id: int, role: str = "member", conn=None) -> int:
        """Add member to chat and return ID"""

        member_id = await self.fetchval(
            f"""INSERT INTO {self._get_table_name()} (chat_id, user_id, role)
                VALUES ($1, $2, $3)
                RETURNING id""",
            chat_id, user_id, role,
            conn=conn
        )

        return member_id

    async def remove_member(self, chat_id: int, user_id: int, conn=None) -> bool:
        """Remove member from chat"""

        result = await self.execute(
            f"DELETE FROM {self._get_table_name()} WHERE chat_id = $1 AND user_id = $2",
            chat_id, user_id,
            conn=conn
        )

        return "DELETE" in result

    async def get_member_role(self, chat_id: int, user_id: int) -> Optional[str]:
        """Get member role in chat"""

        role = await self.fetchval(
            f"SELECT role FROM {self._get_table_name()} WHERE chat_id = $1 AND user_id = $2",
            chat_id, user_id
        )

        return role

    async def is_member(self, chat_id: int, user_id: int) -> bool:
        """Check if user is member of chat"""

        exists = await self.fetchval(
            f"SELECT EXISTS(SELECT 1 FROM {self._get_table_name()} WHERE chat_id = $1 AND user_id = $2)",
            chat_id, user_id
        )

        return exists

    async def get_members_by_chat(self, chat_id: int) -> List[ChatMemberDB]:
        """Get all members of chat"""

        rows = await self.fetch(
            f"SELECT * FROM {self._get_table_name()} WHERE chat_id = $1",
            chat_id
        )

        return [ChatMemberDB(**row) for row in rows]

    async def get_members_by_role(self, chat_id: int, role: str) -> List[ChatMemberDB]:
        """Get members by role (owner, admin, member)"""

        rows = await self.fetch(
            f"SELECT * FROM {self._get_table_name()} WHERE chat_id = $1 AND role = $2",
            chat_id, role
        )

        return [ChatMemberDB(**row) for row in rows]

    async def update_role(self, chat_id: int, user_id: int, role: str, conn=None) -> bool:
        """Update member role"""

        result = await self.execute(
            f"UPDATE {self._get_table_name()} SET role = $1 WHERE chat_id = $2 AND user_id = $3",
            role, chat_id, user_id,
            conn=conn
        )

        return "UPDATE" in result


class ChatService:
    """Service for chat operations"""

    def __init__(self, app: "Application"):
        self.app = app

        self.chat_repo = ChatRepository(app)
        self.member_repo = ChatMemberRepository(app)
