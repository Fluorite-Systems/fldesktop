from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton

from fldesktop.include.menu import Menu


class Applet:
    def __init__(self, comm, package: str = ""):

        self.comm = comm
        self.package = package

        self.callables = {}

        self.widget = QWidget()
        self.qlayout = QVBoxLayout(self.widget)

        self.button = QPushButton(icon=self.get_icon())
        self.button.setObjectName("traybtn")
        self.button.setFlat(True)

        self.menu = Menu(
            self.comm, self.widget, self.button,
            self.comm.request("desktop", "get_instance")
        )

        self.button.clicked.connect(self.show_menu)

        self.comm.request("appletmgr", "add_applet", self)

    def show_menu(self):

        if not self.widget.parent():
            self.menu.layout.addWidget(self.widget)

        self.menu.open()

    def get_icon(self):

        pkgs = self.comm.request("pkgmgr", "get_apps")

        for name, value in pkgs.items():
            if name == self.package:
                return value.icon

        return self.comm.request("iconmgr", "get", "application-generic")

    def delete(self):

        self.comm.request("appletmgr", "del_applet", self)
        self.widget.close()
        self.widget.deleteLater()
        self.menu.close()
        self.menu.deleteLater()
        self.button.close()
        self.button.deleteLater()