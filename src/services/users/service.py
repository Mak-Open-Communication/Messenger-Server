"""User service for account and token operations."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app import Application

from src.services.users.repos import AccountsRepository, TokensRepository
from src.models.api_models import Account, AuthToken, Result


class UserService:
    """Service for user operations."""

    def __init__(self, app: "Application"):
        """Initialize service with application."""

        self.app = app

        self.accounts_repo = AccountsRepository(app)
        self.tokens_repo = TokensRepository(app)

    async def get_user_by_id(self, user_id: int) -> Result[Account]:
        """Get user by ID."""

        account_db = await self.accounts_repo.get_by_id(user_id)
        if not account_db:
            return Result(success=False, error="User not found", error_code="NOT_FOUND")

        # TODO: check is_online via NotifyManager
        is_online = False
        account = self.accounts_repo.to_api_model(account_db, is_online)

        return Result(success=True, data=account)

    async def get_user_by_username(self, username: str) -> Result[Account]:
        """Get user by username."""

        account_db = await self.accounts_repo.get_by_username(username)
        if not account_db:
            return Result(success=False, error="User not found", error_code="NOT_FOUND")

        # TODO: check is_online via NotifyManager
        is_online = False
        account = self.accounts_repo.to_api_model(account_db, is_online)

        return Result(success=True, data=account)

    async def search_users(self, query: str, limit: int = 20) -> Result[list[Account]]:
        """Search users by username."""

        if not query or len(query) < 2:
            return Result(success=False, error="Query too short", error_code="VALIDATION_ERROR")

        accounts_db = await self.accounts_repo.search_by_username(query, limit)

        # TODO: check is_online via NotifyManager
        accounts = [
            self.accounts_repo.to_api_model(acc, is_online=False)
            for acc in accounts_db
        ]

        return Result(success=True, data=accounts)

    async def update_profile(
        self,
        user_id: int,
        display_name: str | None = None
    ) -> Result[Account]:
        """Update user profile."""

        account_db = await self.accounts_repo.get_by_id(user_id)
        if not account_db:
            return Result(success=False, error="User not found", error_code="NOT_FOUND")

        await self.accounts_repo.update(user_id, display_name=display_name)

        updated_account_db = await self.accounts_repo.get_by_id(user_id)
        account = self.accounts_repo.to_api_model(updated_account_db, is_online=True)

        return Result(success=True, data=account)

    async def verify_token(self, token: str) -> Result[bool]:
        """Verify if token is valid."""

        token_db = await self.tokens_repo.get_by_token(token)

        return Result(success=True, data=token_db is not None)
