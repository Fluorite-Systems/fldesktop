from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton

from fldesktop.include.appletmgr.applet import Applet
from fldesktop.include.appletmgr.sidebar import Sidebar

class AppletManager:
    def __init__(self, comm):
        self.comm = comm
        self.comm.register(
            "appletmgr", {
                "add_applet": self.add_applet,
                "del_applet": self.del_applet,
                "enable_sidebar": self.enable_sidebar,
                "disable_sidebar": self.disable_sidebar,
                "toggle_sidebar": self.toggle_sidebar,
                "get_tray": self.get_tray,
                "get_sb_toggle": self.get_sb_toggle
            }
        )

        self.sidebar = Sidebar(self.comm)

        self.tray = QWidget()
        self.tray_l = QHBoxLayout(self.tray)
        self.tray_l.setContentsMargins(0, 0, 0, 0)

        self.sb_toggle = QPushButton(icon=self.comm.request("iconmgr", "get", "sidebar-toggle"))
        self.sb_toggle.setObjectName("traybtn")
        self.sb_toggle.setFlat(True)
        self.sb_toggle.clicked.connect(self.toggle_sidebar)

        self.sbv = False

        self.applets = []

    def add_applet(self, applet: Applet):

        self.applets.append(applet)
        self.tray_l.addWidget(applet.button)
        self.sidebar.add_applet(applet)

    def del_applet(self, applet: Applet):

        ...

    def enable_sidebar(self):

        self.sidebar.show()
        self.tray.hide()

    def disable_sidebar(self):

        self.sidebar.hide()
        self.tray.show()

    def toggle_sidebar(self):

        if not self.sbv:
            self.enable_sidebar()
        else:
            self.disable_sidebar()
        self.sbv = not self.sbv

    def get_tray(self):

        return self.tray

    def get_sb_toggle(self):

        return self.sb_toggle