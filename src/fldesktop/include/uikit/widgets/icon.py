from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap
from fldesktop.include.uikit.widgets.base import Widget


class Icon(Widget):
    def __init__(self, comm, name, attrs):

        self.qwidget = QLabel()

        super().__init__(
            comm, name, attrs,
            {"Attr.UI.Widget.Icon.Icon": ""}
        )

        self.type = "icon"

        self._setup()

        self.pixmap = QPixmap()

    def apply_attrs(self) -> None:
        super().apply_attrs()

        icon = self.comm.request(
            "iconmgr", "parse", self.attrs["Attr.UI.Widget.Icon.Icon"]
        )
        self.qwidget.setPixmap(icon.pixmap(
            self.attrs["width"] if self.attrs["width"] else 64,
            self.attrs["height"] if self.attrs["height"] else 64
        ))
