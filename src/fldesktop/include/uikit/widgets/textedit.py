from PySide6.QtWidgets import QTextEdit
from fldesktop.include.uikit.widgets.base import Widget


class TextEdit(Widget):
    def __init__(self, comm, name, attrs):

        self.qwidget = QTextEdit()

        super().__init__(
            comm, name, attrs,
            {"text": ""}
        )
        
        self.type = "textedit"        

        self.callables = {
            "get_text": self.get_text,
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False)
        }

        self.qwidget.textChanged.connect(
            lambda: self.event(type="textedit_text_changed")
        )

        self._setup()

    def apply_attrs(self):
        super().apply_attrs()

        self.qwidget.setText(self.attrs["text"])

    def get_text(self) -> str:
        return self.qwidget.toPlainText()
