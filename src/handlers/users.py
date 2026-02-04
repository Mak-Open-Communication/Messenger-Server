"""Users transaction handlers."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app import Application

from src.middleware import logging_middleware, AuthMiddleware
from src.services.users import UserService


def register_users_handlers(app: "Application"):
    """Register users handlers."""

    user_service = UserService(app)
    auth = AuthMiddleware(app)

    @app.server.transaction(code="get_user")
    @logging_middleware.log_transaction_debug
    @auth.require_auth
    async def get_user_trans(user_id: int, target_user_id: int):
        """Get user by ID."""

        return await user_service.get_user_by_id(user_id=target_user_id)

    @app.server.transaction(code="search_users")
    @logging_middleware.log_transaction_debug
    @auth.require_auth
    async def search_users_trans(user_id: int, query: str, limit: int = 20):
        """Search users by username."""

        return await user_service.search_users(query=query, limit=limit)

    @app.server.transaction(code="update_profile")
    @logging_middleware.log_transaction
    @auth.require_auth
    async def update_profile_trans(user_id: int, display_name: str | None = None):
        """Update current user profile."""

        return await user_service.update_profile(
            user_id=user_id,
            display_name=display_name
        )

    @app.server.transaction(code="get_my_tokens")
    @logging_middleware.log_transaction_debug
    @auth.require_auth
    async def get_my_tokens_trans(user_id: int, current_token: str):
        """Get all tokens for current user."""

        return await user_service.get_my_tokens(
            user_id=user_id,
            current_token=current_token
        )
