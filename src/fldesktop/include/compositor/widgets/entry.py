from PySide6.QtWidgets import QLineEdit
from fldesktop.include.compositor.widgets.base import Widget


class Entry(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "entry"
        self.qwidget = QLineEdit()

        self.callables = {
            "get_text": self.get_text,
            "set_text": self.set_text,
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False)
        }

        self._setup()

    def get_text(self, _) -> str:
        return self.qwidget.text()

    def set_text(self, args):
        text = args["text"] if "text" in args else ""
        self.qwidget.setText(text)

