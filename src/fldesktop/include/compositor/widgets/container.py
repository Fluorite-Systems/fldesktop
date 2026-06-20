from PySide6.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QHBoxLayout
from fldesktop.include.compositor.widgets.base import Widget
from fldesktop.include.widgets.flowlayout import FlowLayout


class Container(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "container"
        self.qwidget = QScrollArea()

        self.container = QWidget()
        self.qwidget.setWidgetResizable(True)
        self.qwidget.setWidget(self.container)
        if "direction" in self.props:
            if self.props["direction"] == "ver":
                self.qlayout = QVBoxLayout()
            elif self.props["direction"] == "hor":
                self.qlayout = QHBoxLayout()
            elif self.props["direction"] == "flow":
                self.qlayout = FlowLayout()
            else:
                self.qlayout = QVBoxLayout()
        else:
            self.qlayout = QVBoxLayout()
        self.container.setLayout(self.qlayout)

        self._setup()
