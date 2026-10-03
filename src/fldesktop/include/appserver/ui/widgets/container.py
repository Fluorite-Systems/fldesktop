from PySide6.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QHBoxLayout
from fldesktop.include.appserver.ui.widgets.base import Widget
from fldesktop.include.widgets.flowlayout import FlowLayout


class Container(Widget):
    def __init__(self, runner, name, attrs):
        super().__init__(runner, name, attrs)
        self.type = "container"
        self.qwidget = QScrollArea()

        self.container = QWidget()
        self.qwidget.setWidgetResizable(True)
        self.qwidget.setWidget(self.container)
        if "direction" in self.attrs:
            if self.attrs["direction"] == "ver":
                self.qlayout = QVBoxLayout()
            elif self.attrs["direction"] == "hor":
                self.qlayout = QHBoxLayout()
            elif self.attrs["direction"] == "flow":
                self.qlayout = FlowLayout()
            else:
                self.qlayout = QVBoxLayout()
        else:
            self.qlayout = QVBoxLayout()
        self.container.setLayout(self.qlayout)

        self._setup()
