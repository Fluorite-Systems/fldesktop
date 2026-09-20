from PySide6.QtWidgets import QPushButton, QSizePolicy
from PySide6.QtGui import QIcon
from fldesktop.include.appserver.widgets.base import Widget


class Button(Widget):
    def __init__(self, runner, name, props):
        super().__init__(runner, name, props)
        self.type = "Node.UI.Widget.Button"
        self.qwidget = QPushButton()

        self.callables = {
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False) 
        }

        self.base_props = {
            "Attr.UI.Widget.Button.Text": "",
            "Attr.UI.Widget.Button.Icon": "",
            "Attr.UI.Widget.Button.Flat": False,
            "Attr.UI.Widget.Button.Compact": False
        }

        self._setup()

        self.qwidget.clicked.connect(
            lambda: self._runner.event(self, name=self.name, type="button_pressed")
        )

    def apply_props(self):
        super().apply_props()

        if self.props["Attr.UI.Widget.Button.Text"]:
            self.qwidget.setText(
                self.tr(str(self.props["Attr.UI.Widget.Button.Text"]))
            )
        if self.props["Attr.UI.Widget.Button.Icon"]:
            self.qwidget.setIcon(
                QIcon.fromTheme(self.props["Attr.UI.Widget.Button.Icon"])
            )
        if self.props["Attr.UI.Widget.Button.Flat"]:
            self.qwidget.setFlat(self.props["Attr.UI.Widget.Button.Flat"])
        if self.props["Attr.UI.Widget.Button.Compact"]:
            self.qwidget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
