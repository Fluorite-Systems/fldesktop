from PySide6.QtWidgets import QApplication

from fldesktop.include import (communicator, desktop, dialogs,
                     thememgr, pkgmgr, lockscreen, os_manager,
                     configmgr, compositor, search, wm)
from fldesktop.include.compositor.clientmgr import ClientManager
from fldesktop.include.widgets.surface import SurfaceManager

import logging


class Core:
    def __init__(self):
        "There we will do desktop initialization"

        # Init the core first
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s: %(filename)s: %(levelname)s: %(message)s"
        )

        logging.info("Initializing core...")

        self.comm = communicator.Communicator()

        self.app = QApplication()

        self.osmgr = os_manager.OSManager(self.comm)

        self.configmgr = configmgr.ConfigurationManager(self.comm)

        self.pkgmgr = pkgmgr.PackageManager(self.comm)

        self.search = search.Search(self.comm)

        # Setup theming
        self.theming = thememgr.ThemingManager(self.app, self.comm)

        self.surfacemgr = SurfaceManager(self.comm)

        # Init the desktop
        self.desktop = desktop.Desktop(self.comm)

        self.wm = wm.WindowManager(self.comm, self.desktop)

        self.lockscreen = lockscreen.LockScreen(self.desktop, self.comm)

        self.dialogmgr = dialogs.DialogManager(self.desktop, self.comm)

        # Init appserver
        self.clientmgr = ClientManager(self.comm)
        
        self.appserver = compositor.AppServer(self.comm)

        logging.info("Core initialized")

        #self.lockscreen.show_()
        self.comm.send("fade_effect", "fadein")

        # Finally exec the app
        self.app.exec()


if __name__ == "__main__":
    Core()
