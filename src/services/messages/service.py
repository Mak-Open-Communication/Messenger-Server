"""Message service with message, content and tag repositories"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app import Application

from src.services.messages.repos import (
    MessagesRepository,
    MessageContentsRepository,
    MessageTagsRepository,
    UsersFilesRepository
)

from src.models.api_models import Message


class MessageService:
    """Service for messages operations"""

    def __init__(self, app: "Application"):
        self.app = app

        self.messages_repo = MessagesRepository(app)
        self.contents_repo = MessageContentsRepository(app)
        self.tags_repo = MessageTagsRepository(app)

        self.uploaded_files_repo = UsersFilesRepository(app)

    def create_message(self) -> Message:
        pass

    def get_message_by_id(self, message_id: int) -> Message:
        pass
