from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap
from fldesktop.include.compositor.widgets.base import Widget


class Icon(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "icon"
        self.qwidget = QLabel()

        self.base_props = {
            "icon": ""
        }

        self._setup()

        self.pixmap = QPixmap()

    def apply_props(self) -> None:
        super().apply_props()

        icon = self._runner.comm.request(
            "iconmgr", "parse", self.props["icon"]
        )
        self.qwidget.setPixmap(icon.pixmap(
            self.props["width"] if self.props["width"] else 64,
            self.props["height"] if self.props["height"] else 64
        ))
