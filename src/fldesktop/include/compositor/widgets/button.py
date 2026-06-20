from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QIcon
from fldesktop.include.compositor.widgets.base import Widget


class Button(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "button"
        self.qwidget = QPushButton()

        self.callables = {
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False),
            "set_text": lambda t: self.qwidget.setText(str(t))
        }

        self._setup()

        if "text" in self.props:
            self.qwidget.setText(self.tr(str(self.props["text"])))
        if "icon" in self.props:
            self.qwidget.setIcon(QIcon.fromTheme(self.props["icon"]))
        if "flat" in self.props:
            self.qwidget.setFlat(self.props["flat"] == "true")

        self.qwidget.clicked.connect(
            lambda: self._runner.event(name=self.name, type="button_press")
        )
