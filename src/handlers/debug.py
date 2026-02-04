from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app import Application

from src.middleware import logging_middleware


def register_debug_handlers(app: "Application"):
    """Register debug handlers."""

    @app.server.transaction(code="test_connection")
    @logging_middleware.log_transaction
    async def test_connection_trans(simple_data: int) -> int:
        return simple_data
