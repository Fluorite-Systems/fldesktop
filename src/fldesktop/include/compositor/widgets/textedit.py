from PySide6.QtWidgets import QTextEdit
from fldesktop.include.compositor.widgets.base import Widget


class TextEdit(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "textedit"
        self.qwidget = QTextEdit()

        self.callables = {
            "get_text": self.get_text,
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False)
        }

        self.base_props = {
            "text": ""
        }

        self.qwidget.textChanged.connect(
            lambda: self._runner.event(
                name=self.name, type="textedit_text_changed"
            )
        )

        self._setup()

    def apply_props(self):
        super().apply_props()

        self.qwidget.setText(self.props["text"])

    def get_text(self) -> str:
        return self.qwidget.toPlainText()
