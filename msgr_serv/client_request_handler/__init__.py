from libs.htcp import Server

from msgr_serv.client_request_handler.base_transactions import (
    get_api_version_trans
)


def register_transactions(server: Server):
    # Base transactions
    server.transaction(code="get_api_version")(get_api_version_trans)
