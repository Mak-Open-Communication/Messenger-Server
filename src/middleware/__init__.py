from src.middleware.logging_middleware import LoggingMiddleware, setup_logging
from src.middleware.auth_middleware import AuthMiddleware


logging_middleware = LoggingMiddleware()

__all__ = ["LoggingMiddleware", "AuthMiddleware", "setup_logging", "logging_middleware"]
