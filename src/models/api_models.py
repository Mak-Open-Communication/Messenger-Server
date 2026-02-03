"""API models for client responses."""

from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


@dataclass
class Result(Generic[T]):
    """Universal transaction result wrapper."""

    success: bool

    errors: list[tuple[str, str]] # [("AUTH_ERROR", "Token not correct"), ("ARGUMENT_UNCORRECTED", "Arg 'sender'")]
    data: T | None = None


class Account(BaseModel):
    """User account information."""

    account_id: int

    username: str
    display_name: str

    last_online_at: str | None
    in_online: bool

    created_at: str


class AuthToken(BaseModel):
    """Authentication token information."""

    token_id: str
    user_id: int

    token: str
    agent: str | None = None

    is_current: bool
    is_online: bool

    created_at: str


class PersonalTokensList(BaseModel):
    """List of user tokens."""

    tokens: list[AuthToken]


class Chat(BaseModel):
    """Chat information."""

    chat_id: int
    chat_name: str

    owner: Account
    members: list[Account]

    created_at: str


class MessageTag(BaseModel):
    """Message tag for UI effects."""

    tag_id: int
    message_id: int

    for_user: Account | None

    type: str
    tag: str


class MsgContentTextChunk(BaseModel):
    """Message content text chunk."""

    text: str


class MsgContentFile(BaseModel):
    """Message content file."""

    filename: str
    payload: bytes


class Message(BaseModel):
    """Message with sender, contents and tags."""

    message_id: int
    chat_id: int

    sender_user: Account
    is_read: bool

    tags: list[MessageTag]
    contents: list[MsgContentTextChunk | MsgContentFile]

    created_at: str
