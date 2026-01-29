from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app import Application

# from src.middleware import LoggingMiddleware


def register_users_handlers(app: "Application"):
    """Register users handlers."""

    # @app.server.transaction(code="test_connection")
    # @LoggingMiddleware.log_transaction
    # async def test_connection_trans(simple_data: int) -> int:
    #     return simple_data
