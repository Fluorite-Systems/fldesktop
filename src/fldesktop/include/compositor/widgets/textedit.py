from PySide6.QtWidgets import QTextEdit
from fldesktop.include.compositor.widgets.base import Widget


class TextEdit(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "textedit"
        self.qwidget = QTextEdit()

        self.callables = {
            "set_text": self.set_text,
            "get_text": self.get_text,
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False)
        }

        self.qwidget.textChanged.connect(
            lambda: self._runner.event(
                name=self.name, type="textedit_text_changed"
            )
        )

        self._setup()

    def get_text(self) -> str:
        return self.qwidget.toPlainText()

    def set_text(self, text: str) -> None:
        self.qwidget.setPlainText(text)
