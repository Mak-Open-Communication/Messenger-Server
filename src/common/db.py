"""
Database API module for PostgreSQL operations.
"""
import logging
import asyncpg

from typing import Any, Optional, List
from contextlib import asynccontextmanager

from src.config import settings

from src.version import DB_SCHEMA_VERSION


class DatabaseAPI:
    """PostgreSQL database API with connection pooling."""

    def __init__(self):
        """Initialize database API."""

        self.logger = logging.getLogger("db-api")
        self.logger.setLevel(settings.logging_level)

        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """Create connection pool to PostgreSQL."""

        self.pool = await asyncpg.create_pool(
            host=settings.psql_server_host,
            port=settings.psql_server_port,
            user=settings.psql_user,
            password=settings.psql_password,
            database=settings.psql_db,
            min_size=settings.psql_pool_min_size,
            max_size=settings.psql_pool_max_size
        )

    async def safely_connect(self) -> None:
        """Create connection pool to PostgreSQL with exception handling.

        Raises:
            RuntimeError: If critical services fail to start
        """

        try:
            await self.connect()

            db_status = await self.ping()

            if db_status:
                self.logger.info("PostgreSQL connected successfully")
            else:
                raise RuntimeError("PostgreSQL ping failed")

            # Check schema version
            await self._check_schema_version()

        except asyncpg.InvalidPasswordError:
            self.logger.critical("PostgreSQL authentication failed")

            raise RuntimeError("PostgreSQL authentication failed")

        except asyncpg.InvalidCatalogNameError:
            self.logger.critical(f"Database '{settings.psql_db}' does not exist")

            raise RuntimeError(f"Database '{settings.psql_db}' does not exist")

        except Exception as e:
            self.logger.critical(f"Failed to connect to PostgreSQL: {e}")

            raise

    async def _check_schema_version(self):
        """Check database schema version matches expected version.

        Raises:
            RuntimeError: If schema version mismatch or table doesn't exist
        """

        try:
            db_version = await self.fetchval(
                "SELECT version FROM msgr_schema.schema_info LIMIT 1"
            )

            if db_version != DB_SCHEMA_VERSION:
                raise RuntimeError(
                    f"Schema version mismatch: expected {DB_SCHEMA_VERSION}, got {db_version}. "
                    "Please run database migrations."
                )

            self.logger.info(f"Schema version OK: {db_version}")

        except asyncpg.UndefinedTableError:
            raise RuntimeError(
                "Database schema not initialized. Please run latest migrations."
            )

    async def disconnect(self) -> None:
        """Close connection pool."""

        if self.pool:
            await self.pool.close()
            self.pool = None

            self.logger.info("Database disconnected")

    async def ping(self) -> bool:
        """Check database connectivity."""

        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True

        except Exception:
            return False

    @asynccontextmanager
    async def acquire(self):
        """
        Acquire connection from pool.

        Usage:
            async with db_api.acquire() as conn:
                await conn.execute(...)
        """

        async with self.pool.acquire() as conn:
            yield conn

    async def execute(self, query: str, *args) -> str:
        """
        Execute SQL query without returning data.

        Args:
            query: SQL query with $1, $2... placeholders
            *args: Query parameters

        Returns:
            Status string (e.g., "INSERT 0 1")
        """

        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """
        Fetch single row.

        Args:
            query: SQL query with $1, $2... placeholders
            *args: Query parameters

        Returns:
            Single row as Record or None
        """

        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """
        Fetch multiple rows.

        Args:
            query: SQL query with $1, $2... placeholders
            *args: Query parameters

        Returns:
            List of Records
        """

        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchval(self, query: str, *args, column: int = 0) -> Any:
        """
        Fetch single value.

        Args:
            query: SQL query with $1, $2... placeholders
            *args: Query parameters
            column: Column index (default: 0)

        Returns:
            Single value
        """

        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args, column=column)

    async def executemany(self, query: str, args_list: List[tuple]) -> None:
        """
        Execute query multiple times with different parameters.

        Args:
            query: SQL query with $1, $2... placeholders
            args_list: List of parameter tuples
        """

        async with self.pool.acquire() as conn:
            await conn.executemany(query, args_list)

    async def execute_script(self, script: str) -> None:
        """
        Execute SQL script (multiple statements).

        Args:
            script: SQL script text
        """

        async with self.pool.acquire() as conn:
            await conn.execute(script)

    @asynccontextmanager
    async def transaction(self):
        """
        Transaction context manager.

        Usage:
            async with db_api.transaction() as conn:
                await conn.execute("INSERT ...")
                await conn.execute("UPDATE ...")
        """

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn
