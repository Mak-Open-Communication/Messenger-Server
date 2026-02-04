"""Subscription handlers."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app import Application

from src.middleware import logging_middleware


def register_subscription_handlers(app: "Application"):
    """Register subscription handlers."""

    @app.server.subscription(event_type="subscribe")
    @logging_middleware.log_subscription
    async def user_subscribe(token: str):
        """Subscribe to user events (new messages, typing, etc.)."""

        async for event in app.notify_man.subscribe(token):
            yield {"type": event.type, "data": event.data}
