"""
Main application class with lifecycle management.
"""

import logging

from typing import Optional

from src.middleware.logging_middleware import setup_logging

from src.common.db import DatabaseAPI
from src.common.s3 import S3API
from src.common.notify_manager import NotifyManager

from src.handlers import register_handlers
from src.htcp.aio_server import AsyncServer

from src.config import settings


class Application:
    """Main application class."""

    def __init__(self):
        """Initialize application components."""
        setup_logging()

        self.logger = logging.getLogger("msgr-core")
        self.logger.setLevel(settings.logging_level)

        self.db: DatabaseAPI = DatabaseAPI()
        self.s3: S3API = S3API()

        self.notify_man: NotifyManager = NotifyManager(self)

        self.server: Optional[AsyncServer] = None

        self.logger.info("Application initialized")

    async def startup(self) -> None:
        """
        Startup routine: connect to database and S3.

        Raises:
            RuntimeError: If critical services fail to start
        """

        self.logger.info("Starting server:")

        await self.db.safely_connect()

        await self.s3.safely_connect()

        self.logger.info("Application startup complete")

    async def shutdown(self) -> None:
        """Shutdown routine: disconnect from services."""
        self.logger.info("Shutting down application:")

        if self.db.pool:
            await self.db.disconnect()
            self.logger.info("Database disconnected")

        if self.s3.session:
            await self.s3.disconnect()
            self.logger.info("S3 disconnected")

        if self.server:
            await self.server.down()
            self.logger.info("HTCP server stopped")

        self.logger.info("Application shutdown complete")

    def create_server(self) -> AsyncServer:
        """
        Create and configure HTCP server.

        Returns:
            Configured AsyncServer instance
        """

        self.server = AsyncServer(
            name="htcp-server",
            host=settings.host,
            port=settings.port,
            max_connections=settings.max_connections,
            expose_transactions=settings.expose_transactions,
            logger=logging.getLogger("htcp.server"),
        )

        register_handlers(app=self)

        return self.server
