from libs.htcp import Server

from msgr_serv.client_request_handler.transactions import (
    get_welcome_trans
)


def register_transactions(server: Server):
    # Debug
    server.transaction(code="get_welcome")(get_welcome_trans)
