"""API models for client responses"""

from pydantic import BaseModel
from typing import List, Optional, Union


class Account(BaseModel):
    """User account information"""

    account_id: int

    username: str
    display_name: str

    last_online_at: str
    in_online: bool

    created_at: str


class AuthToken(BaseModel):
    """Authentication token information"""

    token_id: str
    user_id: int

    token: str
    agent: Optional[str] = None

    is_current: bool
    is_online: bool

    created_at: str


class PersonalTokensList(BaseModel):
    """List of user tokens"""

    tokens: List[AuthToken]


class Chat(BaseModel):
    """Chat information"""

    chat_id: int
    chat_name: str

    owner: Account
    members: List[Account]

    created_at: str


class MessageTag(BaseModel):
    """Message tag for UI effects"""

    tag_id: int
    message_id: int

    for_user: Account

    type: str
    tag: str


class MsgContentTextChunk(BaseModel):
    """Message content text"""

    text: str


class MsgContentFile(BaseModel):
    """Message content file"""

    filename: str
    payload: bytes


class Message(BaseModel):
    """Message with sender, contents and tags"""

    message_id: int
    chat_id: int

    sender_user: Account
    is_read: bool

    tags: List[MessageTag]
    contents: List[Union[MsgContentTextChunk, MsgContentFile]]

    created_at: str


class ErrorResponse(BaseModel):
    """Error response for client errors"""

    error: str
    message: str
    details: Optional[list] = None
