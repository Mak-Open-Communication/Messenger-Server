"""
Production entry point for Messenger HTCP Server.
"""

import asyncio
import sys
import logging

from src.app import Application
from src.config import settings


async def main():
    """Main entry point."""

    app = Application()

    try:
        await app.startup()
        server = app.create_server()

        app.logger.info("Starting HTCP server...")

        await server.up()

    except KeyboardInterrupt:
        app.logger.info("Received interrupt signal")

    finally:
        await app.shutdown()


if __name__ == "__main__":
    logger = logging.getLogger("app-starter")

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        pass

    except Exception:
        if settings.showing_tracebacks:
            import traceback
            traceback.print_exc()
        else:
            logger.critical(
                "Critical unexpected error. Enable the 'showing_tracebacks' parameter in your .env file for debugging.")
        sys.exit(1)
