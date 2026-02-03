import sys
import logging
import time

from functools import wraps
from pathlib import Path
from typing import Callable

from src.config import settings


def setup_logging() -> None:
    """Configure logging based on settings."""

    log_level = getattr(logging, settings.logging_level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Suppress noisy third-party loggers
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("aiobotocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if enabled)
    if settings.logging_on_file:
        logs_dir = Path(settings.logs_dir)
        logs_dir.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(
            logs_dir / "app.log",
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


class LoggingMiddleware:
    """Logging transactions/subscriptions middleware."""

    def __init__(self):
        self.logger = logging.getLogger("request-logger")
        self.logger.setLevel(settings.logging_level)

    @staticmethod
    def _sanitize_params(params: dict) -> dict:
        """
        Removes sensitive data from parameters before logging
        """
        sensitive_keys = {"password", "password_hash", "token", "secret", "api_key", "private_key"}

        sanitized = {}
        for key, value in params.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value

        return sanitized

    def _transaction_decorator(self, func: Callable, level: int) -> Callable:
        """Base decorator for logging transactions."""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            transaction_name = func.__name__
            user_id = kwargs.get("user_id", "anonymous")
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                self.logger.log(
                    level,
                    f"[user:{user_id}] Transaction '{transaction_name}' completed [{duration:.3f}s]"
                )

                return result

            except Exception as e:
                duration = time.time() - start_time

                self.logger.error(
                    f"[user:{user_id}] Transaction '{transaction_name}' failed: "
                    f"{type(e).__name__}: {e} [{duration:.3f}s]",
                    exc_info=True
                )

                raise

        return wrapper

    def log_transaction(self, func: Callable) -> Callable:
        """Decorator for logging transactions at INFO level."""

        return self._transaction_decorator(func, logging.INFO)

    def log_transaction_debug(self, func: Callable) -> Callable:
        """Decorator for logging transactions at DEBUG level."""

        return self._transaction_decorator(func, logging.DEBUG)

    def _subscription_decorator(self, func: Callable, level: int) -> Callable:
        """Base decorator for logging subscriptions."""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            subscription_name = func.__name__
            user_id = kwargs.get("user_id", "anonymous")

            self.logger.log(
                level,
                f"[user:{user_id}] Subscription '{subscription_name}' started"
            )

            try:
                async for item in func(*args, **kwargs):
                    yield item

            except GeneratorExit:
                self.logger.log(
                    level,
                    f"[user:{user_id}] Subscription '{subscription_name}' closed"
                )

            except Exception as e:
                self.logger.error(
                    f"[user:{user_id}] Subscription '{subscription_name}' error: "
                    f"{type(e).__name__}: {e}",
                    exc_info=True
                )
                raise

        return wrapper

    def log_subscription(self, func: Callable) -> Callable:
        """Decorator for logging subscriptions at INFO level."""

        return self._subscription_decorator(func, logging.INFO)

    def log_subscription_debug(self, func: Callable) -> Callable:
        """Decorator for logging subscriptions at DEBUG level."""

        return self._subscription_decorator(func, logging.DEBUG)
