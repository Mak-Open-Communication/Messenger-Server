from msgr_serv.server.app import MessengerServer


def run_repl(args):
    repl = MessengerServer(args=args)
    repl.startup()
