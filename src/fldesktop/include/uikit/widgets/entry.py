from PySide6.QtWidgets import QLineEdit
from fldesktop.include.uikit.widgets.base import Widget


class Entry(Widget):
    def __init__(self, runner, name, attrs):
        super().__init__(runner, name, attrs)
        self.type = "entry"
        self.qwidget = QLineEdit()

        self.callables = {
            "get_text": self.get_text,
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False)
        }

        self.base_attrs = {
            "text": ""
        }

        self._setup()

    def apply_attrs(self):
        super().apply_attrs()

        self.qwidget.setText(self.attrs["text"])

    def get_text(self, _) -> str:
        return self.qwidget.text()
