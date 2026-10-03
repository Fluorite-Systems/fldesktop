from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap
from fldesktop.include.appserver.ui.widgets.base import Widget


class Icon(Widget):
    def __init__(self, runner, name, attrs):
        super().__init__(runner, name, attrs)
        self.type = "icon"
        self.qwidget = QLabel()

        self.base_attrs = {
            "Attr.UI.Widget.Icon.Icon": ""
        }

        self._setup()

        self.pixmap = QPixmap()

    def apply_attrs(self) -> None:
        super().apply_attrs()

        icon = self._runner.comm.request(
            "iconmgr", "parse", self.attrs["Attr.UI.Widget.Icon.Icon"]
        )
        self.qwidget.setPixmap(icon.pixmap(
            self.attrs["width"] if self.attrs["width"] else 64,
            self.attrs["height"] if self.attrs["height"] else 64
        ))
