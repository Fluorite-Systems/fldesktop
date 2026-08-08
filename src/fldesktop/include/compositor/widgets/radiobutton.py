from PySide6.QtWidgets import QRadioButton
from fldesktop.include.compositor.widgets.base import Widget


class RadioButton(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "radiobutton"
        self.qwidget = QRadioButton()

        self.callables = {
            "select": self.select,
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False)
        }

        self._setup()            

        self.qwidget.toggled.connect(
            lambda c: self._runner.event(
                name=self.name, type="radiobutton_selected"
            ) if c else lambda: ...
        )

    def apply_props(self):
        super().apply_props()

        self.qwidget.setText(self.tr(str(self.props["text"])))

    def select(self, _):
        self.qwidget.blockSignals(True)
        self.qwidget.setChecked(True)
        self.qwidget.blockSignals(False)
