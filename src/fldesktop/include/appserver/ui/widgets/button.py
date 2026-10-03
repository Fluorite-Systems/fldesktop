from PySide6.QtWidgets import QPushButton, QSizePolicy
from PySide6.QtGui import QIcon
from fldesktop.include.appserver.ui.widgets.base import Widget


class Button(Widget):
    def __init__(self, runner, name, attrs):
        super().__init__(runner, name, attrs)
        self.type = "Node.UI.Widget.Button"
        self.qwidget = QPushButton()

        self.callables = {
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False) 
        }

        self.base_attrs = {
            "Attr.UI.Widget.Button.Text": "",
            "Attr.UI.Widget.Button.Icon": "",
            "Attr.UI.Widget.Button.Flat": False,
            "Attr.UI.Widget.Button.Compact": False
        }

        self._setup()

        self.qwidget.clicked.connect(
            lambda: self._runner.event(self, name=self.name, type="button_pressed")
        )

    def apply_attrs(self):
        super().apply_attrs()

        if self.attrs["Attr.UI.Widget.Button.Text"]:
            self.qwidget.setText(
                self.tr(str(self.attrs["Attr.UI.Widget.Button.Text"]))
            )
        if self.attrs["Attr.UI.Widget.Button.Icon"]:
            self.qwidget.setIcon(
                QIcon.fromTheme(self.attrs["Attr.UI.Widget.Button.Icon"])
            )
        if self.attrs["Attr.UI.Widget.Button.Flat"]:
            self.qwidget.setFlat(self.attrs["Attr.UI.Widget.Button.Flat"])
        if self.attrs["Attr.UI.Widget.Button.Compact"]:
            self.qwidget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
