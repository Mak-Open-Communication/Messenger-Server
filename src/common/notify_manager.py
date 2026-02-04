"""NotifyManager for handling subscriptions and event broadcasting."""

import asyncio
import logging

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, AsyncGenerator

if TYPE_CHECKING:
    from src.app import Application

from src.services.chats.repos import ChatMembersRepository

from src.config import settings


@dataclass
class Event:
    """Event to be sent to users."""

    type: str
    data: dict[str, Any]


class NotifyManager:
    """Manages user subscriptions and event broadcasting."""

    def __init__(self, app: "Application"):
        """Initialize NotifyManager."""

        self.app = app
        self.logger = logging.getLogger("notify-manager")
        self.logger.setLevel(settings.logging_level)

        # user_id -> {token -> queue}
        self._subscriptions: dict[int, dict[str, asyncio.Queue[Event]]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, token: str) -> AsyncGenerator[Event, None]:
        """
        Subscribe user by token. Returns async generator yielding events.

        Used as HTCP subscription handler.
        """

        from src.services.users.repos import TokensRepository

        tokens_repo = TokensRepository(self.app)
        token_db = await tokens_repo.get_by_token(token)

        if not token_db:
            self.logger.warning(f"Subscribe attempt with invalid token")
            return

        user_id = token_db.user_id
        queue: asyncio.Queue[Event] = asyncio.Queue()

        # Register subscription
        async with self._lock:
            if user_id not in self._subscriptions:
                self._subscriptions[user_id] = {}
                # First subscription for this user - notify user_online
                await self._broadcast_user_online(user_id)

            self._subscriptions[user_id][token] = queue

        self.logger.info(f"User {user_id} subscribed with token {token[:8]}...")

        try:
            while True:
                event = await queue.get()
                yield event

        except asyncio.CancelledError:
            pass

        finally:
            await self._unsubscribe(user_id, token)

    async def _unsubscribe(self, user_id: int, token: str) -> None:
        """Unsubscribe user's token and handle cleanup."""

        from src.services.users.repos import AccountsRepository

        async with self._lock:
            if user_id in self._subscriptions:
                self._subscriptions[user_id].pop(token, None)

                # If no more subscriptions for this user
                if not self._subscriptions[user_id]:
                    del self._subscriptions[user_id]

        # Update last_online_at
        accounts_repo = AccountsRepository(self.app)
        await accounts_repo.update_last_online(user_id)

        # Notify user_offline
        await self._broadcast_user_offline(user_id)

        self.logger.info(f"User {user_id} unsubscribed token {token[:8]}...")

    def is_online(self, user_id: int) -> bool:
        """Check if user is online (has any active subscription)."""

        return user_id in self._subscriptions and len(self._subscriptions[user_id]) > 0

    def get_online_user_ids(self) -> list[int]:
        """Get list of all online user IDs."""

        return list(self._subscriptions.keys())

    async def notify_user(self, user_id: int, event: Event) -> None:
        """Send event to all user's devices."""

        async with self._lock:
            if user_id not in self._subscriptions:
                return

            for queue in self._subscriptions[user_id].values():
                await queue.put(event)

    async def notify_users(self, user_ids: list[int], event: Event) -> None:
        """Send event to multiple users."""

        for user_id in user_ids:
            await self.notify_user(user_id, event)

    async def notify_chat(self, chat_id: int, event: Event, exclude_user_id: int | None = None) -> None:
        """Send event to all members of a chat."""

        members_repo = ChatMembersRepository(self.app)
        member_ids = await members_repo.get_member_user_ids(chat_id)

        for user_id in member_ids:
            if exclude_user_id and user_id == exclude_user_id:
                continue
            await self.notify_user(user_id, event)

    # Event builders

    async def _broadcast_user_online(self, user_id: int) -> None:
        """Broadcast user_online event to relevant users."""

        from src.services.chats.repos import ChatsRepository

        chats_repo = ChatsRepository(self.app)
        chats = await chats_repo.get_chats_by_user(user_id)

        event = Event(type="user_online", data={"user_id": user_id})

        # Notify all users who share chats with this user
        notified: set[int] = set()
        for chat in chats:
            from src.services.chats.repos import ChatMembersRepository
            members_repo = ChatMembersRepository(self.app)
            member_ids = await members_repo.get_member_user_ids(chat.id)

            for member_id in member_ids:
                if member_id != user_id and member_id not in notified:
                    await self.notify_user(member_id, event)
                    notified.add(member_id)

    async def _broadcast_user_offline(self, user_id: int) -> None:
        """Broadcast user_offline event to relevant users."""

        from src.services.chats.repos import ChatsRepository

        chats_repo = ChatsRepository(self.app)
        chats = await chats_repo.get_chats_by_user(user_id)

        event = Event(type="user_offline", data={"user_id": user_id})

        # Notify all users who share chats with this user
        notified: set[int] = set()
        for chat in chats:
            from src.services.chats.repos import ChatMembersRepository
            members_repo = ChatMembersRepository(self.app)
            member_ids = await members_repo.get_member_user_ids(chat.id)

            for member_id in member_ids:
                if member_id != user_id and member_id not in notified:
                    await self.notify_user(member_id, event)
                    notified.add(member_id)

    # Public event senders

    async def send_new_message(
        self,
        chat_id: int,
        sender_user_id: int,
        sender_username: str,
        chat_name: str,
        message_id: int,
        message_preview: str
    ) -> None:
        """Send new_message event to chat members."""

        event = Event(
            type="new_message",
            data={
                "sender_username": sender_username,
                "chat_name": chat_name,
                "sender_user_id": sender_user_id,
                "chat_id": chat_id,
                "message_id": message_id,
                "message_content": message_preview[:61]
            }
        )
        await self.notify_chat(chat_id, event, exclude_user_id=sender_user_id)

    async def send_message_edited(self, chat_id: int, message_id: int, editor_user_id: int) -> None:
        """Send message_edited event to chat members."""

        event = Event(
            type="message_edited",
            data={"chat_id": chat_id, "message_id": message_id, "editor_user_id": editor_user_id}
        )
        await self.notify_chat(chat_id, event)

    async def send_message_deleted(self, chat_id: int, message_id: int, deleter_user_id: int) -> None:
        """Send message_deleted event to chat members."""

        event = Event(
            type="message_deleted",
            data={"chat_id": chat_id, "message_id": message_id, "deleter_user_id": deleter_user_id}
        )
        await self.notify_chat(chat_id, event)

    async def send_chat_created(self, chat_id: int, chat_name: str, creator_user_id: int) -> None:
        """Send chat_created event to chat members."""

        event = Event(
            type="chat_created",
            data={"chat_id": chat_id, "chat_name": chat_name, "creator_user_id": creator_user_id}
        )
        await self.notify_chat(chat_id, event)

    async def send_member_added(self, chat_id: int, added_user_id: int, adder_user_id: int) -> None:
        """Send member_added event to chat members."""

        event = Event(
            type="member_added",
            data={"chat_id": chat_id, "added_user_id": added_user_id, "adder_user_id": adder_user_id}
        )
        await self.notify_chat(chat_id, event)

    async def send_member_removed(self, chat_id: int, removed_user_id: int, remover_user_id: int) -> None:
        """Send member_removed event to chat members."""

        event = Event(
            type="member_removed",
            data={"chat_id": chat_id, "removed_user_id": removed_user_id, "remover_user_id": remover_user_id}
        )
        await self.notify_chat(chat_id, event)

        # Also notify the removed user
        await self.notify_user(removed_user_id, event)

    async def send_typing(self, chat_id: int, user_id: int) -> None:
        """Send typing event to chat members."""

        event = Event(
            type="typing",
            data={"chat_id": chat_id, "user_id": user_id}
        )
        await self.notify_chat(chat_id, event, exclude_user_id=user_id)

    async def send_read_status(self, chat_id: int, message_id: int, reader_user_id: int) -> None:
        """Send read_status event to chat members."""

        event = Event(
            type="read_status",
            data={"chat_id": chat_id, "message_id": message_id, "reader_user_id": reader_user_id}
        )
        await self.notify_chat(chat_id, event)
