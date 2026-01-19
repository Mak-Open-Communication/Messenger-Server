"""
Media server configuration.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Media server settings."""

    # Server settings
    host: str = "0.0.0.0"
    port: int = 4207

    # S3 settings
    endpoint_url: str = "<endpoint>"
    access_key = "<access-key>"
    secret_key = "<secret-key>"
    bucket_name = "<bkt>"

    # Logging
    log_level: str = "DEBUG"

    class Config:
        env_file = ".env"
        env_prefix = "MEDIA_"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
