from PySide6.QtWidgets import QLineEdit
from fldesktop.include.compositor.widgets.base import Widget


class Entry(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "entry"
        self.qwidget = QLineEdit()

        self.callables = {
            "get_text": self.get_text,
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False)
        }

        self.base_props = {
            "text": ""
        }

        self._setup()

    def apply_props(self):
        super().apply_props()

        self.qwidget.setText(self.props["text"])

    def get_text(self, _) -> str:
        return self.qwidget.text()
