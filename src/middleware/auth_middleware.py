"""Authentication middleware for token validation."""

from functools import wraps
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from src.app import Application

from src.services.users.repos import TokensRepository
from src.models.api_models import Result


class AuthMiddleware:
    """Middleware for token-based authentication."""

    def __init__(self, app: "Application"):
        """Initialize with application."""

        self.app = app
        self.tokens_repo = TokensRepository(app)

    def require_auth(self, func: Callable) -> Callable:
        """Decorator requiring valid token. Extracts user_id from token."""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            token = kwargs.get("token")
            if not token:
                return Result(
                    success=False,
                    error="Token required",
                    error_code="UNAUTHORIZED"
                )

            token_db = await self.tokens_repo.get_by_token(token)
            if not token_db:
                return Result(
                    success=False,
                    error="Invalid token",
                    error_code="UNAUTHORIZED"
                )

            kwargs.pop("token")
            kwargs["user_id"] = token_db.user_id

            return await func(*args, **kwargs)

        return wrapper
