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
    psql_db: str = "-"
    psql_user: str = "-"
    psql_password: str = "-"

    # S3 Server settings
    s3_endpoint_url: str = "<endpoint>"
    s3_access_key: str = "<access-key>"
    s3_secret_key: str = "<secret-key>"
    s3_bucket_name: str = "<bkt>"

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
