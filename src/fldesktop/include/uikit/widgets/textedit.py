from PySide6.QtWidgets import QTextEdit
from fldesktop.include.uikit.widgets.base import Widget


class TextEdit(Widget):
    def __init__(self, comm, name, attrs):

        self.qwidget = QTextEdit()

        super().__init__(
            comm, name, attrs
        )
        
        self.type = "textedit"        

        self.callables = {
            "get_text": self.get_text,
            "set_text": self.set_text,
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False)
        }

        self.qwidget.textChanged.connect(
            lambda: self.event(type="textedit_text_changed")
        )

        self._setup()

    def set_text(self, text: str):
        self.qwidget.setText(str(text))

    def get_text(self) -> str:
        return self.qwidget.toPlainText()
