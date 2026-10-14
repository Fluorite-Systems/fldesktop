from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PySide6.QtGui import QIcon

from fldesktop.include.menu import Menu
from fldesktop.include.uikit.ui import UI


class Applet(UI):
    def __init__(self, comm, name, attrs):
        super().__init__(comm, name, attrs, {
            "Attr.UI.Applet.ButtonText": "",
            "Attr.UI.Applet.Package": "",
            "Attr.UI.Applet.ButtonIcon": "",
            "Attr.UI.Applet.QIcon": QIcon()
        })

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

        self.apply_attrs()

        self.comm.request("appletmgr", "add_applet", self)

    def show_menu(self):

        if not self.widget.parent():
            self.menu.layout.addWidget(self.widget)

        self.menu.open()

    def get_icon(self):

        pkgs = self.comm.request("pkgmgr", "get_apps")

        for name, value in pkgs.items():
            if name == self.attrs["Attr.UI.Applet.Package"]:
                return value.icon

        return self.comm.request("iconmgr", "get", "application-generic")

    def apply_attrs(self):
        super().apply_attrs()

        if not hasattr(self, "button"): # dirty hacck
            return

        self.button.setText(self.attrs["Attr.UI.Applet.ButtonText"])

        if self.attrs["Attr.UI.Applet.ButtonIcon"]:
            self.button.setIcon(
                self.comm.request(
                    "iconmgr", "parse",
                    self.attrs["Attr.UI.Applet.ButtonIcon"]
                )
            )
        elif not self.attrs["Attr.UI.Applet.QIcon"].isNull():
            self.button.setIcon(self.attrs["Attr.UI.Applet.QIcon"])
        elif self.attrs["Attr.UI.Applet.ButtonText"]:
            self.button.setIcon(QIcon())
        else:
            self.button.setIcon(self.get_icon())

    def delete(self):

        self.comm.request("appletmgr", "del_applet", self)
        self.widget.close()
        self.widget.deleteLater()
        self.menu.filter.remove()
        self.menu.filter.deleteLater()
        self.menu.close()
        self.menu.deleteLater()
        self.button.close()
        self.button.deleteLater()