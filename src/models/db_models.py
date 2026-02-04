"""PostgreSQL Database models."""

from datetime import datetime

from pydantic import BaseModel as BaseDBModel


class AccountDB(BaseDBModel):
    """Account database model."""

    id: int

    username: str
    display_name: str
    password_hash: str

    last_online_at: datetime | None

    account_is_active: bool

    created_at: datetime


class TokenDB(BaseDBModel):
    """Token database model."""

    id: int
    user_id: int

    token: str
    agent: str | None

    created_at: datetime


class ChatDB(BaseDBModel):
    """Chat database model."""

    id: int

    owner_user_id: int
    chat_name: str

    created_at: datetime


class ChatMemberDB(BaseDBModel):
    """Chat member database model."""

    id: int

    user_id: int
    chat_id: int

    role: str


class MessageDB(BaseDBModel):
    """Message database model."""

    id: int
    chat_id: int

    sender_user_id: int
    is_read: bool

    created_at: datetime


class MessageContentDB(BaseDBModel):
    """Message content database model."""

    id: int
    message_id: int

    resource_name: str

    type: str
    content: str


class MessageTagDB(BaseDBModel):
    """Message tag database model."""

    id: int
    message_id: int

    for_user_id: int | None

    type: str
    tag: str
