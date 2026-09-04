# fldesktop - FluoriteOS graphical environment
# Copyright (C) 2025-2026 Iamha111
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.


from fldesktop.include.init import Init
from fldesktop.include.args import ArgumentParser

from pathlib import Path

import logging
import sys


VERSION = "raw"
LOGGING_DIR = Path("/system/logs")


class Core:
    def __init__(self) -> None:
        "Basic initialization"

        self.ap = ArgumentParser()

        if self.ap.args.version:
            print(VERSION)
            sys.exit()

        if LOGGING_DIR.exists():
            logging.basicConfig(
                level=logging.DEBUG if self.ap.args.debug else logging.INFO,
                format="%(asctime)s: %(filename)s: %(levelname)s: %(message)s",
                filename=LOGGING_DIR / "fldesktop.log",
                filemode="w"
            )
        else:
            logging.basicConfig(
                level=logging.DEBUG if self.ap.args.debug else logging.INFO,
                format="%(asctime)s: %(filename)s: %(levelname)s: %(message)s"
            )

        logging.info(f"Welcome to fldesktop, version: {VERSION}")

        self.init = Init()
        self.init.run()


if __name__ == "__main__":
    Core()
