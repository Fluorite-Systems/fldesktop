from PySide6.QtWidgets import QApplication

from fldesktop.include import (communicator, desktop, dialogs,
                     thememgr, pkgmgr, lockscreen, os_manager,
                     configmgr, compositor, search, wm, loginmgr,
                     localemgr, notifications, iconmgr)
from fldesktop.include.compositor.clientmgr import ClientManager
from fldesktop.include.widgets.surface import SurfaceManager
from fldesktop.include.input import InputManager

from fldesktop.include.init import Init

import logging


VERSION = "raw"


class Core:
    def __init__(self) -> None:
        "Basic initialization"

        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s: %(filename)s: %(levelname)s: %(message)s"
        )

        logging.info(f"Welcome to fldesktop, version: {VERSION}")

        self.init = Init()
        self.init.run()

    def __init__bk(self) -> None:
        "There we will do desktop initialization. Backup."

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

        self.localemgr = localemgr.LocaleManager(self.comm)

        self.pkgmgr = pkgmgr.PackageManager(self.comm)

        self.search = search.Search(self.comm)

        self.loginmgr = loginmgr.LoginManager(self.comm)

        self.inputmgr = InputManager(self.comm)

        # Setup theming
        self.theming = thememgr.ThemingManager(self.comm)

        self.iconmgr = iconmgr.IconManager(self.comm)

        self.surfacemgr = SurfaceManager(self.comm)

        # Init the desktop
        self.desktop = desktop.Desktop(self.comm)

        self.wm = wm.WindowManager(self.comm)

        self.lockscreen = lockscreen.LockScreen(self.comm)

        self.dialogmgr = dialogs.DialogManager(self.comm)

        self.notifymgr = notifications.NotificationManager(self.comm)

        # Init appserver
        self.clientmgr = ClientManager(self.comm)
        
        self.appserver = compositor.AppServer(self.comm)

        logging.info("Core initialized")

        self.lockscreen.show_()
        self.comm.send("fade_effect", "fadein")

        self.comm.send("notifymgr", "notify", "system", "hello")

        # Finally exec the app
        self.app.exec()


if __name__ == "__main__":
    Core()
