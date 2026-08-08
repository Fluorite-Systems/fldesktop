from PySide6.QtWidgets import QCheckBox
from fldesktop.include.compositor.widgets.base import Widget


class CheckBox(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "checkbox"
        self.qwidget = QCheckBox()

        self.callables = {
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False)
        }

        self.base_props = {"text": ""}

        self._setup()

    def apply_props(self):
        super().apply_props()

        if self.props["text"]:
            self.qwidget.setText(self.tr(str(self.props["text"])))
