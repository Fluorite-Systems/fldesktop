from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton

from fldesktop.include.uikit.applet import Applet
from fldesktop.include.appletmgr.sidebar import Sidebar
from fldesktop.include.appletmgr.std_applets import APPLETS


class AppletManager:
    def __init__(self, comm):
        self.comm = comm
        self.comm.register(
            "appletmgr", {
                "add_applet": self.add_applet,
                "del_applet": self.del_applet,
                "show_sidebar": self.show_sidebar,
                "hide_sidebar": self.hide_sidebar,
                "toggle_sidebar": self.toggle_sidebar,
                "is_sidebar_visible": self.is_sidebar_visible,
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

        self.show_sidebar()

        self.applets = []

        self.load_std_applets()

    def load_std_applets(self):

        for applet in APPLETS:
            self.applets.append(applet(self.comm))

    def add_applet(self, applet: Applet):

        self.applets.append(applet)
        self.tray_l.addWidget(applet.button)
        self.sidebar.add_applet(applet)

    def del_applet(self, applet: Applet):

        if applet not in self.applets:
            return

        self.sidebar.del_applet(applet)
        self.applets.remove(applet)

    def show_sidebar(self):

        self.sbv = True
        self.comm.emit("sidebar_state_changed")
        self.sidebar.show()
        self.tray.hide()

    def hide_sidebar(self):

        self.sbv = False
        self.comm.emit("sidebar_state_changed")
        self.sidebar.hide()
        self.tray.show()

    def toggle_sidebar(self):

        if not self.sbv:
            self.show_sidebar()
        else:
            self.hide_sidebar()

    def is_sidebar_visible(self):

        return self.sbv

    def get_tray(self):

        return self.tray

    def get_sb_toggle(self):

        return self.sb_toggle