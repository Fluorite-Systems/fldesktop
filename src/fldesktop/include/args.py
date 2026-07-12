import argparse


class ArgumentParser:
    def __init__(self):

        parser = argparse.ArgumentParser(
            description="FluoriteOS graphical environment"
        )

        parser.add_argument(
            "-d", "--debug", action="store_true",
            help="show debug messages in log"
        )

        parser.add_argument(
            "-v", "--version", action="store_true",
            help="show version and exit"
        )

        self.args = parser.parse_args()
