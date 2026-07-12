from fldesktop.include.init import Init
from fldesktop.include.args import ArgumentParser

import logging
import sys


VERSION = "raw"


class Core:
    def __init__(self) -> None:
        "Basic initialization"

        self.ap = ArgumentParser()

        if self.ap.args.version:
            print(VERSION)
            sys.exit()

        logging.basicConfig(
            level=logging.DEBUG if self.ap.args.debug else logging.INFO,
            format="%(asctime)s: %(filename)s: %(levelname)s: %(message)s"
        )

        logging.info(f"Welcome to fldesktop, version: {VERSION}")

        self.init = Init()
        self.init.run()


if __name__ == "__main__":
    Core()
