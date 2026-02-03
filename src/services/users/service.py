"""User service for account and token operations."""

import json
import hashlib
from dataclasses import dataclass
from uuid import uuid4
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app import Application

from src.services.users.repos import AccountsRepository, TokensRepository
from src.models.api_models import Account, AuthToken, Result


@dataclass
class LoginResult:
    """Result of successful login."""

    account: Account
    token: AuthToken


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
            return Result(success=False, errors=[("NOT_FOUND", "User not found")])

        # TODO: check is_online via NotifyManager
        is_online = False
        account = self.accounts_repo.to_api_model(account_db, is_online)

        return Result(success=True, errors=[], data=account)

    async def get_user_by_username(self, username: str) -> Result[Account]:
        """Get user by username."""

        account_db = await self.accounts_repo.get_by_username(username)
        if not account_db:
            return Result(success=False, errors=[("NOT_FOUND", "User not found")])

        # TODO: check is_online via NotifyManager
        is_online = False
        account = self.accounts_repo.to_api_model(account_db, is_online)

        return Result(success=True, errors=[], data=account)

    async def search_users(self, query: str, limit: int = 20) -> Result[list[Account]]:
        """Search users by username."""

        if not query or len(query) < 2:
            return Result(success=False, errors=[("VALIDATION_ERROR", "Query too short")])

        accounts_db = await self.accounts_repo.search_by_username(query, limit)

        # TODO: check is_online via NotifyManager
        accounts = [
            self.accounts_repo.to_api_model(acc, is_online=False)
            for acc in accounts_db
        ]

        return Result(success=True, errors=[], data=accounts)

    async def update_profile(
        self,
        user_id: int,
        display_name: str | None = None
    ) -> Result[Account]:
        """Update user profile."""

        account_db = await self.accounts_repo.get_by_id(user_id)
        if not account_db:
            return Result(success=False, errors=[("NOT_FOUND", "User not found")])

        await self.accounts_repo.update(user_id, display_name=display_name)

        updated_account_db = await self.accounts_repo.get_by_id(user_id)
        account = self.accounts_repo.to_api_model(updated_account_db, is_online=True)

        return Result(success=True, errors=[], data=account)

    async def verify_token(self, token: str) -> Result[bool]:
        """Verify if token is valid."""

        token_db = await self.tokens_repo.get_by_token(token)

        return Result(success=True, errors=[], data=token_db is not None)

    @staticmethod
    def _generate_token(username: str, agent: str) -> str:
        """Generate auth token."""

        payload = json.dumps({
            "username": username,
            "agent": agent,
            "salt": str(uuid4())
        })

        return hashlib.sha256(payload.encode()).hexdigest()

    async def register(
        self,
        username: str,
        display_name: str,
        password_hash: str,
        agent: str
    ) -> Result[LoginResult]:
        """Register new account and return token."""

        if await self.accounts_repo.username_exists(username):
            return Result(success=False, errors=[("VALIDATION_ERROR", "Username already taken")])

        account_id = await self.accounts_repo.create(
            username=username,
            password_hash=password_hash,
            display_name=display_name
        )

        token = self._generate_token(username, agent)
        await self.tokens_repo.create(
            user_id=account_id,
            token=token,
            agent=agent
        )

        account_db = await self.accounts_repo.get_by_id(account_id)
        account = self.accounts_repo.to_api_model(account_db, is_online=True)

        token_db = await self.tokens_repo.get_by_token(token)
        auth_token = self.tokens_repo.to_api_model(token_db, is_current=True, is_online=True)

        return Result(success=True, errors=[], data=LoginResult(account=account, token=auth_token))

    async def login(
        self,
        username: str,
        password_hash: str,
        agent: str
    ) -> Result[LoginResult]:
        """Login and return token."""

        account_db = await self.accounts_repo.get_by_username(username)
        if not account_db:
            return Result(success=False, errors=[("UNAUTHORIZED", "Invalid username or password")])

        if account_db.password_hash != password_hash:
            return Result(success=False, errors=[("UNAUTHORIZED", "Invalid username or password")])

        if not account_db.account_is_active:
            return Result(success=False, errors=[("FORBIDDEN", "Account is deactivated")])

        token = self._generate_token(username, agent)
        await self.tokens_repo.create(
            user_id=account_db.id,
            token=token,
            agent=agent
        )

        account = self.accounts_repo.to_api_model(account_db, is_online=True)

        token_db = await self.tokens_repo.get_by_token(token)
        auth_token = self.tokens_repo.to_api_model(token_db, is_current=True, is_online=True)

        return Result(success=True, errors=[], data=LoginResult(account=account, token=auth_token))

    async def logout(self, user_id: int, target_token: str) -> Result[None]:
        """Logout by deleting token."""

        deleted = await self.tokens_repo.delete_by_user_and_token(user_id, target_token)
        if not deleted:
            return Result(success=False, errors=[("NOT_FOUND", "Token not found")])

        return Result(success=True, errors=[], data=None)

    async def get_my_tokens(self, user_id: int, current_token: str) -> Result[list[AuthToken]]:
        """Get all tokens for user."""

        tokens_db = await self.tokens_repo.get_by_user_id(user_id)

        # TODO: check is_online via NotifyManager
        tokens = [
            self.tokens_repo.to_api_model(
                token_db,
                is_current=(token_db.token == current_token),
                is_online=False
            )
            for token_db in tokens_db
        ]

        return Result(success=True, errors=[], data=tokens)
