from PySide6.QtWidgets import QRadioButton
from fldesktop.include.uikit.widgets.base import Widget


class RadioButton(Widget):
    def __init__(self, comm, name, attrs):

        self.qwidget = QRadioButton()

        super().__init__(
            comm, name, attrs,
            {"Attr.UI.Widget.RadioButton.Text": ""}
        )

        self.type = "radiobutton"

        self.callables = {
            "select": self.select,
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False)
        }

        self._setup()            

        self.qwidget.toggled.connect(self._handle_toggle)

    def _handle_toggle(self, checked: bool):
        
        if checked:
            self.event(type="radiobutton_selected")

    def apply_attrs(self):
        super().apply_attrs()

        self.qwidget.setText(
            self.tr(str(self.attrs["Attr.UI.Widget.RadioButton.Text"]))
        )

    def select(self):
        self.qwidget.blockSignals(True)
        self.qwidget.setChecked(True)
        self.qwidget.blockSignals(False)
