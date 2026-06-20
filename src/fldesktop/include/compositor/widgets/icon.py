from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap, QIcon
from fldesktop.include.compositor.widgets.base import Widget


class Icon(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "icon"
        self.qwidget = QLabel()

        self.callables = {
            "set_icon": self.set_icon
        }

        self._setup()

        self.pixmap = QPixmap()

        if "icon" in self.props:
            self.set_icon({
                "icon": self.props["icon"],
                "width": self.props["width"]\
                    if "width" in self.props else 64,
                "height": self.props["height"]\
                    if "height" in self.props else 64,
            })

    def set_icon(self, args: dict) -> None:
        icon = QIcon.fromTheme(
            args["icon"] if "icon" in args else "none"
        )
        self.qwidget.setPixmap(icon.pixmap(
            args["width"] if "width" in args else 64,
            args["height"] if "height" in args else 64
        ))
