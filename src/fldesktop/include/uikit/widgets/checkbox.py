from PySide6.QtWidgets import QCheckBox
from fldesktop.include.uikit.widgets.base import Widget


class CheckBox(Widget):
    def __init__(self, comm, name, attrs):

        self.qwidget = QCheckBox()

        super().__init__(
            comm, name, attrs,
            {"text": ""}
        )

        self.type = "checkbox"

        self.callables = {
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False)
        }

        self._setup()

    def apply_attrs(self):
        super().apply_attrs()

        if self.attrs["text"]:
            self.qwidget.setText(self.tr(str(self.attrs["text"])))
