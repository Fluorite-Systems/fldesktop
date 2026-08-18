from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from fldesktop.include.compositor.widgets.base import Widget


class Label(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "label"
        self.qwidget = QLabel()

        self.callables = {
            "get_text": self.get_text
        }

        self.base_props = {
            "text": "",
            "alignment": "center",
            "style": "normal"
        }

        self.qwidget.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed
        )

        self._setup()

    def apply_props(self):
        super().apply_props()

        self.qwidget.setText(self.tr(str(self.props["text"])))

        if self.props["alignment"] == "left":
            self.qwidget.setAlignment(Qt.AlignmentFlag.AlignLeft)
        elif self.props["alignment"] == "right":
            self.qwidget.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            self.qwidget.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        styles = {
            "caption": QFont("Noto Sans", 14, QFont.Bold),
            "header": QFont("Noto Sans", 12, QFont.Bold),
            "subheader": QFont("Noto Sans", 10, QFont.Bold),
            "normal": QFont("Noto Sans", 10)
        }

        if self.props["style"] in styles:
            self.qwidget.setFont(styles[self.props["style"]])
        else:
            self.qwidget.setFont(styles["normal"])

    def get_text(self) -> str:
        return self.qwidget.toPlainText()

