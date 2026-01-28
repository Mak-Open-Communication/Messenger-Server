import logging

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app import Application


from src.config import settings


class DatabaseService:
    def __init__(self, app: "Application"):
        self.logger = logging.getLogger("db-service")
        self.logger.setLevel(settings.logging_level)

        self.app = app


class BaseRepository:
    repository_name = "notifies"
    table_model = None

    def __init__(self, app: "Application"):
        self.logger = logging.getLogger(f"{self.repository_name}-repo")
        self.logger.setLevel(settings.logging_level)

        self.app = app

        self.db_service = DatabaseService(app=app)
