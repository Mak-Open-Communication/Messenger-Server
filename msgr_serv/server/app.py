import logging

from libs.htcp import Server

from msgr_serv.common.utils import create_required_dirs
from msgr_serv.client_request_handler import register_transactions

from msgr_serv.config import settings
from msgr_serv.version import (
    VERSION,
    VERSION_NAME,
    VERSION_ID,
    API_VERSION
)


class MessengerServer:
    def __init__(self, args):
        self.args = args

        self.logger: logging.Logger | None = None

        self.server: Server | None = None

        create_required_dirs()

        self.configure_logging()
        self.configure_htcp_endpoint()

    def configure_logging(self):
        logging.basicConfig(
            level=settings.logging_level,
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[
                logging.FileHandler(filename="logs/server.log", encoding="utf-8", mode="a"),
                logging.StreamHandler()
            ]
        )

        self.logger = logging.getLogger("msgr-core")

    def configure_htcp_endpoint(self):
        server_logger = logging.getLogger("msgr-server")
        server_logger.setLevel(settings.logging_level)

        self.server = Server(
            name="moc-messenger",
            host=str(settings.host),
            port=int(settings.port),
            max_connections=int(settings.max_connections),
            expose_transactions=bool(settings.expose_transactions),
            logger=server_logger
        )

    def startup(self):
        register_transactions(server=self.server)

        self.server.up()

    def shutdown(self):
        pass
