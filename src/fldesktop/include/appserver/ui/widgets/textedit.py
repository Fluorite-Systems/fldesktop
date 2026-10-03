from PySide6.QtWidgets import QTextEdit
from fldesktop.include.appserver.ui.widgets.base import Widget


class TextEdit(Widget):
    def __init__(self, runner, name, attrs):
        super().__init__(runner, name, attrs)
        self.type = "textedit"
        self.qwidget = QTextEdit()

        self.callables = {
            "get_text": self.get_text,
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False)
        }

        self.base_attrs = {
            "text": ""
        }

        self.qwidget.textChanged.connect(
            lambda: self._runner.event(
                self,
                name=self.name, type="textedit_text_changed"
            )
        )

        self._setup()

    def apply_attrs(self):
        super().apply_attrs()

        self.qwidget.setText(self.attrs["text"])

    def get_text(self) -> str:
        return self.qwidget.toPlainText()
