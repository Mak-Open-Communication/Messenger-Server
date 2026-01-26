from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app import Application

from src.handlers.debug import register_debug_handlers

# from src.handlers.auth import register_auth_handlers
# from src.handlers.user import register_user_handlers
# from src.handlers.devices import register_devices_handlers

# from src.handlers.chats import register_chat_handlers
# from src.handlers.messages import register_messages_handlers


def register_handlers(app: "Application"):
    """Register all handlers."""

    register_debug_handlers(app=app)
