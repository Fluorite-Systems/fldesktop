from PySide6.QtWidgets import QLineEdit
from fldesktop.include.uikit.widgets.base import Widget


class Entry(Widget):
    def __init__(self, comm, name, attrs):

        self.qwidget = QLineEdit()

        super().__init__(
            comm, name, attrs,
            {"text": ""}
        )

        self.type = "entry"
        

        self.callables = {
            "get_text": self.get_text,
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False)
        }

        self._setup()

    def apply_attrs(self):
        super().apply_attrs()

        self.qwidget.setText(self.attrs["text"])

    def get_text(self, _) -> str:
        return self.qwidget.text()
