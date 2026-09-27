from PySide6.QtWidgets import QCheckBox
from fldesktop.include.appserver.widgets.base import Widget


class CheckBox(Widget):
    def __init__(self, runner, name, attrs):
        super().__init__(runner, name, attrs)
        self.type = "checkbox"
        self.qwidget = QCheckBox()

        self.callables = {
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False)
        }

        self.base_attrs = {"text": ""}

        self._setup()

    def apply_attrs(self):
        super().apply_attrs()

        if self.attrs["text"]:
            self.qwidget.setText(self.tr(str(self.attrs["text"])))
