"""API models for client responses"""

from pydantic import BaseModel
from typing import List, Optional


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
    admins: List[Account]
    members: List[Account]

    created_at: str


class MessageTag(BaseModel):
    """Message tag for UI effects"""

    tag_id: int
    message_id: int

    type: str
    tag: str


class MessageContent(BaseModel):
    """Message content (text or file)"""

    content_id: int
    message_id: int

    resource_name: str

    type: str
    content: str


class Message(BaseModel):
    """Message with sender, contents and tags"""

    message_id: int
    chat_id: int

    is_read: bool
    sender: Account

    tags: List[MessageTag]
    contents: List[MessageContent]

    created_at: str


class MessagesList(BaseModel):
    """List of messages"""

    messages: List[Message]


class ErrorResponse(BaseModel):
    """Error response for client errors"""

    error: str
    message: str
    details: Optional[dict] = None


# Auth handler responses
class RegisterResponse(BaseModel):
    """Response for register endpoint"""

    success: bool
    account_id: int


class LoginResponse(BaseModel):
    """Response for login endpoint"""

    success: bool

    token: str
    account: Account


class LogoutResponse(BaseModel):
    """Response for logout endpoint"""

    success: bool


class ValidateTokenResponse(BaseModel):
    """Response for validate_token endpoint"""

    valid: bool


class GetMyTokensResponse(BaseModel):
    """Response for get_my_tokens endpoint"""

    success: bool
    tokens: PersonalTokensList


# User handler responses
class GetProfileResponse(BaseModel):
    """Response for get_profile endpoint"""

    success: bool
    account: Account


class UpdateProfileResponse(BaseModel):
    """Response for update_profile endpoint"""

    success: bool
    account: Account


# Chat handler responses
class CreateChatResponse(BaseModel):
    """Response for create_chat endpoint"""

    success: bool
    chat: Chat


class GetMyChatsResponse(BaseModel):
    """Response for get_my_chats endpoint"""

    success: bool
    chats: List[Chat]


class GetChatInfoResponse(BaseModel):
    """Response for get_chat_info endpoint"""

    success: bool
    chat: Chat


class AddMemberResponse(BaseModel):
    """Response for add_member endpoint"""

    success: bool


class RemoveMemberResponse(BaseModel):
    """Response for remove_member endpoint"""

    success: bool


class LeaveChatResponse(BaseModel):
    """Response for leave_chat endpoint"""

    success: bool


class UpdateChatResponse(BaseModel):
    """Response for update_chat endpoint"""

    success: bool
    chat: Chat


# Message handler responses
class SendMessageResponse(BaseModel):
    """Response for send_message endpoint"""

    success: bool
    message: Message


class GetMessagesResponse(BaseModel):
    """Response for get_messages endpoint"""

    success: bool
    messages: MessagesList


class MarkReadResponse(BaseModel):
    """Response for mark_read endpoint"""

    success: bool


class EditMessageResponse(BaseModel):
    """Response for edit_message endpoint"""

    success: bool
    message: Message


class DeleteMessageResponse(BaseModel):
    """Response for delete_message endpoint"""

    success: bool
