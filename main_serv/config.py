"""
Server configuration.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Server settings."""

    # Server settings
    server_host: str = "0.0.0.0"
    server_port: int = 4207
    server_passwd: str = "" # If string empty, then no password

    # Usage media server
    media_serv_host: str = "localhost"
    media_serv_port: int = 4205

    # Logging
    log_level: str = "DEBUG"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
