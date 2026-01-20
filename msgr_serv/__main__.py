import argparse

from . import run_repl


def starter():
    parser = argparse.ArgumentParser(description="MOC Messenger Server")

    parser.add_argument(
        "-c", "--config",
        type=str,
        help="Path to the configuration file"
    )

    args = parser.parse_args()
    run_repl(args=args)


if __name__ == "__main__":
    starter()
