from PySide6.QtWidgets import QRadioButton
from fldesktop.include.appserver.widgets.base import Widget


class RadioButton(Widget):
    def __init__(self, runner, name, props):
        super().__init__(runner, name, props)
        self.type = "radiobutton"
        self.qwidget = QRadioButton()

        self.callables = {
            "select": self.select,
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False)
        }

        self.base_props = {
            "Attr.UI.Widget.RadioButton.Text": ""
        }

        self._setup()            

        self.qwidget.toggled.connect(self._handle_toggle)

    def _handle_toggle(self, checked: bool):
        
        if checked:
            self._runner.event(
                self,
                name=self.name, type="radiobutton_selected"
            )

    def apply_props(self):
        super().apply_props()

        self.qwidget.setText(
            self.tr(str(self.props["Attr.UI.Widget.RadioButton.Text"]))
        )

    def select(self):
        self.qwidget.blockSignals(True)
        self.qwidget.setChecked(True)
        self.qwidget.blockSignals(False)
