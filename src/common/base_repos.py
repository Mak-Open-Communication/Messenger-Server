"""Base repository classes for data access"""

import logging

from typing import TYPE_CHECKING, Optional, Any

if TYPE_CHECKING:
    from src.app import Application

from src.config import settings


class BaseDBRepository:
    """Base class for database repositories"""

    repository_name = "base"
    table_name = None
    schema_name = "msgr_schema"

    def __init__(self, app: "Application"):
        self.logger = logging.getLogger(f"{self.repository_name}-repo")
        self.logger.setLevel(settings.logging_level)

        self.app = app
        self.db = self.app.db

    def _get_table_name(self) -> str:
        """Get full table name with schema"""

        if not self.table_name:
            raise ValueError(f"table_name not set for {self.__class__.__name__}")

        return f"{self.schema_name}.{self.table_name}"

    async def execute(self, query: str, *args, conn=None) -> str:
        """Execute query without returning data"""

        if conn:
            return await conn.execute(query, *args)

        return await self.db.execute(query, *args)

    async def fetchrow(self, query: str, *args, conn=None) -> Optional[Any]:
        """Fetch single row"""

        if conn:
            return await conn.fetchrow(query, *args)

        return await self.db.fetchrow(query, *args)

    async def fetch(self, query: str, *args, conn=None) -> list:
        """Fetch multiple rows"""

        if conn:
            return await conn.fetch(query, *args)

        return await self.db.fetch(query, *args)

    async def fetchval(self, query: str, *args, conn=None) -> Any:
        """Fetch single value"""

        if conn:
            return await conn.fetchval(query, *args)

        return await self.db.fetchval(query, *args)


class BaseS3Repository:
    """Base class for S3 repositories"""

    repository_name = "base"
    resources_dir = ""

    def __init__(self, app: "Application"):
        self.logger = logging.getLogger(f"{self.repository_name}-repo")
        self.logger.setLevel(settings.logging_level)

        self.app = app
        self.s3 = self.app.s3

    def _get_full_key(self, key: str) -> str:
        """Get full S3 key with resources_dir prefix"""

        return f"{self.resources_dir}{key}"
