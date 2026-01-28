from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Account:
    account_id: int
    username: str

    online_at: str
    in_online: bool

    created_at: str


@dataclass
class AuthToken:
    token_id: str

    user_id: int # For user
    token: str

    created_at: str

    is_current: bool


@dataclass
class PersonalTokensList:
    tokens: List[AuthToken]


@dataclass
class Chat:
    chat_id: int
    chat_name: str

    owner: Account
    admins: List[Account]
    members: List[Account]

    created_at: str


@dataclass
class MessageTag:
    tag_id: int
    message_id: int # For message

    type: str # Show-Message-UI-Effect
    tag: str # FireEffect


@dataclass
class MessageContent:
    content_id: int
    message_id: int # For message

    resource_name: str # DB, S3
    type: str # Text, File
    content: str # S3 File url; For text max 1024 symbols


@dataclass
class Message:
    message_id: int
    chat_id: int # For chat

    is_read: bool # Message is read mark
    sender: Account

    tags: List[MessageTag]
    contents: List[MessageContent]

    created_at: str


@dataclass
class MessagesList:
    messages: List[Message]


@dataclass
class AuthCredentials:
    username: Optional[str]
    password: Optional[str]
    token: Optional[str]
