from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from fldesktop.include.appserver.widgets.base import Widget


class Label(Widget):
    def __init__(self, runner, name, props):
        super().__init__(runner, name, props)
        self.type = "label"
        self.qwidget = QLabel()

        self.callables = {
            "get_text": self.get_text
        }

        self.base_props = {
            "Attr.UI.Widget.Label.Text": "",
            "Attr.UI.Widget.Label.Alignment": "center",
            "Attr.UI.Widget.Label.Style": "normal"
        }

        self.qwidget.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed
        )

        self._setup()

    def apply_props(self):
        super().apply_props()

        self.qwidget.setText(self.tr(str(self.props["Attr.UI.Widget.Label.Text"])))

        if self.props["Attr.UI.Widget.Label.Alignment"] == "left":
            self.qwidget.setAlignment(Qt.AlignmentFlag.AlignLeft)
        elif self.props["Attr.UI.Widget.Label.Alignment"] == "right":
            self.qwidget.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            self.qwidget.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        styles = {
            "caption": QFont("Noto Sans", 14, QFont.Bold),
            "header": QFont("Noto Sans", 12, QFont.Bold),
            "subheader": QFont("Noto Sans", 10, QFont.Bold),
            "normal": QFont("Noto Sans", 10)
        }

        if self.props["Attr.UI.Widget.Label.Style"] in styles:
            self.qwidget.setFont(
                styles[self.props["Attr.UI.Widget.Label.Style"]]
            )
        else:
            self.qwidget.setFont(styles["normal"])

    def get_text(self) -> str:
        return self.qwidget.toPlainText()

