"""User repositories for account and token operations."""

from datetime import datetime, timezone, timedelta

from src.common.base_repos import BaseDBRepository
from src.models.db_models import AccountDB, TokenDB
from src.models.api_models import Account, AuthToken


UTC_PLUS_3 = timezone(timedelta(hours=3))


class AccountsRepository(BaseDBRepository):
    """Repository for account operations."""

    repository_name = "accounts"
    table_name = "accounts"

    async def get_by_id(self, account_id: int) -> AccountDB | None:
        """Get account by ID."""

        row = await self.fetchrow(
            f"SELECT * FROM {self._get_table_name()} WHERE id = $1",
            account_id
        )

        return AccountDB(**row) if row else None

    async def get_by_username(self, username: str) -> AccountDB | None:
        """Get account by username."""

        row = await self.fetchrow(
            f"SELECT * FROM {self._get_table_name()} WHERE username = $1",
            username
        )

        return AccountDB(**row) if row else None

    async def create(
        self,
        username: str,
        password_hash: str,
        display_name: str,
        conn=None
    ) -> int:
        """Create new account and return ID."""

        account_id = await self.fetchval(
            f"""INSERT INTO {self._get_table_name()}
                (username, password_hash, display_name, account_is_active)
                VALUES ($1, $2, $3, true)
                RETURNING id""",
            username, password_hash, display_name,
            conn=conn
        )

        return account_id

    async def update(
        self,
        account_id: int,
        username: str | None = None,
        display_name: str | None = None,
        conn=None
    ) -> bool:
        """Update account fields."""

        updates = []
        params = []
        param_idx = 1

        if username is not None:
            updates.append(f"username = ${param_idx}")
            params.append(username)
            param_idx += 1

        if display_name is not None:
            updates.append(f"display_name = ${param_idx}")
            params.append(display_name)
            param_idx += 1

        if not updates:
            return False

        params.append(account_id)
        await self.execute(
            f"UPDATE {self._get_table_name()} SET {', '.join(updates)} WHERE id = ${param_idx}",
            *params,
            conn=conn
        )

        return True

    async def update_last_online(self, account_id: int, conn=None) -> None:
        """Update last_online_at timestamp."""

        await self.execute(
            f"UPDATE {self._get_table_name()} SET last_online_at = $1 WHERE id = $2",
            datetime.now(timezone.utc),
            account_id,
            conn=conn
        )

    async def username_exists(self, username: str) -> bool:
        """Check if username already exists."""

        exists = await self.fetchval(
            f"SELECT EXISTS(SELECT 1 FROM {self._get_table_name()} WHERE username = $1)",
            username
        )

        return exists

    async def search_by_username(self, query: str, limit: int = 20) -> list[AccountDB]:
        """Search accounts by username pattern."""

        rows = await self.fetch(
            f"""SELECT * FROM {self._get_table_name()}
                WHERE username ILIKE $1 AND account_is_active = true
                ORDER BY username
                LIMIT $2""",
            f"%{query}%", limit
        )

        return [AccountDB(**row) for row in rows]

    @staticmethod
    def to_api_model(account_db: AccountDB, is_online: bool) -> Account:
        """Convert DB model to API model."""

        if is_online:
            last_online_at = datetime.now(UTC_PLUS_3).isoformat()
        elif account_db.last_online_at:
            last_online_at = account_db.last_online_at.isoformat()
        else:
            last_online_at = account_db.created_at.isoformat()

        return Account(
            account_id=account_db.id,
            username=account_db.username,
            display_name=account_db.display_name,
            last_online_at=last_online_at,
            in_online=is_online,
            created_at=account_db.created_at.isoformat()
        )


class TokensRepository(BaseDBRepository):
    """Repository for token operations."""

    repository_name = "tokens"
    table_name = "tokens"

    async def get_by_token(self, token: str) -> TokenDB | None:
        """Get token by value."""

        row = await self.fetchrow(
            f"SELECT * FROM {self._get_table_name()} WHERE token = $1",
            token
        )

        return TokenDB(**row) if row else None

    async def get_by_user_id(self, user_id: int) -> list[TokenDB]:
        """Get all tokens for user."""

        rows = await self.fetch(
            f"SELECT * FROM {self._get_table_name()} WHERE user_id = $1 ORDER BY created_at DESC",
            user_id
        )

        return [TokenDB(**row) for row in rows]

    async def create(
        self,
        user_id: int,
        token: str,
        agent: str | None = None,
        conn=None
    ) -> int:
        """Create new token and return ID."""

        token_id = await self.fetchval(
            f"""INSERT INTO {self._get_table_name()} (user_id, token, agent)
                VALUES ($1, $2, $3)
                RETURNING id""",
            user_id, token, agent,
            conn=conn
        )

        return token_id

    async def delete(self, token: str, conn=None) -> bool:
        """Delete token."""

        result = await self.execute(
            f"DELETE FROM {self._get_table_name()} WHERE token = $1",
            token,
            conn=conn
        )

        return "DELETE" in result

    async def delete_by_user_and_token(
        self,
        user_id: int,
        token: str,
        conn=None
    ) -> bool:
        """Delete token for specific user."""

        result = await self.execute(
            f"DELETE FROM {self._get_table_name()} WHERE user_id = $1 AND token = $2",
            user_id, token,
            conn=conn
        )

        return "DELETE" in result

    @staticmethod
    def to_api_model(
        token_db: TokenDB,
        is_current: bool,
        is_online: bool
    ) -> AuthToken:
        """Convert DB model to API model."""

        return AuthToken(
            token_id=str(token_db.id),
            user_id=token_db.user_id,
            token=token_db.token,
            created_at=token_db.created_at.isoformat(),
            is_current=is_current,
            is_online=is_online,
            agent=token_db.agent
        )
