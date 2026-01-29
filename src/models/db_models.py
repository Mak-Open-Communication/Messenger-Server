"""PostgreSQL Database models"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AccountDB(BaseModel):
    """Account database model"""

    id: int

    username: str
    display_name: str
    password_hash: str

    account_is_active: bool

    created_at: datetime


class TokenDB(BaseModel):
    """Token database model"""

    id: int
    user_id: int

    token: str
    agent: Optional[str] = None

    created_at: datetime


class ChatDB(BaseModel):
    """Chat database model"""

    id: int

    owner: int
    name: str

    created_at: datetime


class ChatMemberDB(BaseModel):
    """Chat member database model"""
    id: int
    user_id: int
    chat_id: int
    role: str


class MessageDB(BaseModel):
    """Message database model"""

    id: int
    chat_id: int

    sender: int
    is_read: bool

    created_at: datetime


class MessageContentDB(BaseModel):
    """Message content database model"""

    id: int
    message_id: int

    resource_name: str

    type: str
    content: Optional[str] = None


class MessageTagDB(BaseModel):
    """Message tag database model"""

    id: int
    message_id: int

    type: str
    tag: Optional[str] = None
