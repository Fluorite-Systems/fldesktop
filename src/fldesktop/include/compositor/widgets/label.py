from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from fldesktop.include.compositor.widgets.base import Widget


class Label(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "label"
        self.qwidget = QLabel()

        self.callables = {
            "set_text": self.set_text,
            "get_text": self.get_text
        }

        self._setup()

        if "text" in self.props:
            self.qwidget.setText(self.tr(str(self.props["text"])))
        if "alignment" in self.props:
            if self.props["alignment"] == "left":
                self.qwidget.setAlignment(Qt.AlignmentFlag.AlignLeft)
            elif self.props["alignment"] == "right":
                self.qwidget.setAlignment(Qt.AlignmentFlag.AlignRight)
            else:
                self.qwidget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if "style" in self.props:
            styles = {
                "caption": QFont("Noto Sans", 14, QFont.Bold),
                "header": QFont("Noto Sans", 12, QFont.Bold),
                "subheader": QFont("Noto Sans", 10, QFont.Bold)
            }
            if self.props["style"] in styles:
                self.qwidget.setFont(styles[self.props["style"]])

    def get_text(self) -> str:
        return self.qwidget.toPlainText()

    def set_text(self, text: str) -> None:
        self.qwidget.setText(text)
