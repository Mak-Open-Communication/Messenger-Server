"""
Server configuration.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Server settings."""

    # Server settings
    host: str = "0.0.0.0"
    port: int = 4207
    max_connections: int = 128
    expose_transactions: bool = True

    # PostgreSQL Server settings
    psql_server_host: str = "localhost"
    psql_server_port: int = 5432
    psql_db: str = "messenger_main_db"
    psql_user: str = "messenger_app"
    psql_password: str = "mycoolmessenger"

    # Usage media server
    media_serv_host: str = "localhost"
    media_serv_port: int = 4205
    media_serv_api_key: str = "<key>"

    # Logging
    logging_level: str = "DEBUG"
    logging_on_file: bool = True
    logs_dir: str = "logs"

    class Config:
        env_file = ".env"
        # env_prefix = "MAIN_"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
