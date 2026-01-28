import logging

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app import Application


from src.config import settings


class BaseDBRepository:
    repository_name = "notifies"
    table_model = None

    def __init__(self, app: "Application"):
        self.logger = logging.getLogger(f"{self.repository_name}-repo")
        self.logger.setLevel(settings.logging_level)

        self.app = app

        self.db = self.app.db


    def get_records(self, find_filters: dict) -> list:
        pass

    def add_record(self, record) -> bool:
        pass

class BaseS3Repository:
    repository_name: str = "avatars"

    resources_dir: str = "users/avatars/"

    def __init__(self, app: "Application"):
        self.logger = logging.getLogger(f"{self.repository_name}-repo")
        self.logger.setLevel(settings.logging_level)

        self.app = app

        self.s3 = self.app.s3
