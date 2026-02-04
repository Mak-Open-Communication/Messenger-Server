"""Auth transaction handlers."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app import Application

from src.middleware import logging_middleware, AuthMiddleware
from src.services.users import UserService


def register_auth_handlers(app: "Application"):
    """Register auth handlers."""

    user_service = UserService(app)
    auth = AuthMiddleware(app)

    @app.server.transaction(code="register")
    @logging_middleware.log_transaction
    async def register_trans(
        username: str,
        visible_name: str,
        password_hash: str,
        agent: str
    ):
        """Register new user and return token + account."""

        return await user_service.register(
            username=username,
            display_name=visible_name,
            password_hash=password_hash,
            agent=agent
        )

    @app.server.transaction(code="login")
    @logging_middleware.log_transaction
    async def login_trans(
        username: str,
        password_hash: str,
        agent: str
    ):
        """Login and return token + account."""

        return await user_service.login(
            username=username,
            password_hash=password_hash,
            agent=agent
        )

    @app.server.transaction(code="logout")
    @logging_middleware.log_transaction
    @auth.require_auth
    async def logout_trans(user_id: int, target_token: str):
        """Logout by deleting target token."""

        return await user_service.logout(
            user_id=user_id,
            target_token=target_token
        )

    @app.server.transaction(code="verify_token")
    @logging_middleware.log_transaction
    @auth.require_auth
    async def verify_token_trans(user_id: int, target_token: str):
        """Verify if target token is valid."""

        return await user_service.verify_token(token=target_token)
