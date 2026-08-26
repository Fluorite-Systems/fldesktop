from PySide6.QtWidgets import QPushButton, QSizePolicy
from PySide6.QtGui import QIcon
from fldesktop.include.compositor.widgets.base import Widget


class Button(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "button"
        self.qwidget = QPushButton()

        self.callables = {
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False) 
        }

        self.base_props = {
            "text": "",
            "icon": "",
            "flat": False,
            "compact": False
        }

        self._setup()

        self.qwidget.clicked.connect(
            lambda: self._runner.event(name=self.name, type="button_pressed")
        )

    def apply_props(self):
        super().apply_props()

        if self.props["text"]:
            self.qwidget.setText(self.tr(str(self.props["text"])))
        if self.props["icon"]:
            self.qwidget.setIcon(QIcon.fromTheme(self.props["icon"]))
        if self.props["flat"]:
            self.qwidget.setFlat(self.props["flat"])
        if self.props["compact"]:
            self.qwidget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
