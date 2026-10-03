from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from fldesktop.include.appserver.ui.widgets.base import Widget


class Label(Widget):
    def __init__(self, runner, name, attrs):
        super().__init__(runner, name, attrs)
        self.type = "label"
        self.qwidget = QLabel()

        self.callables = {
            "get_text": self.get_text
        }

        self.base_attrs = {
            "Attr.UI.Widget.Label.Text": "",
            "Attr.UI.Widget.Label.Alignment": "center",
            "Attr.UI.Widget.Label.Style": "normal"
        }

        self.qwidget.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed
        )

        self._setup()

    def apply_attrs(self):
        super().apply_attrs()

        self.qwidget.setText(self.tr(str(self.attrs["Attr.UI.Widget.Label.Text"])))

        if self.attrs["Attr.UI.Widget.Label.Alignment"] == "left":
            self.qwidget.setAlignment(Qt.AlignmentFlag.AlignLeft)
        elif self.attrs["Attr.UI.Widget.Label.Alignment"] == "right":
            self.qwidget.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            self.qwidget.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        styles = {
            "caption": QFont("Noto Sans", 14, QFont.Bold),
            "header": QFont("Noto Sans", 12, QFont.Bold),
            "subheader": QFont("Noto Sans", 10, QFont.Bold),
            "normal": QFont("Noto Sans", 10)
        }

        if self.attrs["Attr.UI.Widget.Label.Style"] in styles:
            self.qwidget.setFont(
                styles[self.attrs["Attr.UI.Widget.Label.Style"]]
            )
        else:
            self.qwidget.setFont(styles["normal"])

    def get_text(self) -> str:
        return self.qwidget.toPlainText()

