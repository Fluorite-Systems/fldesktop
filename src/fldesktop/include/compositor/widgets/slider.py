from PySide6.QtWidgets import QSlider
from fldesktop.include.compositor.widgets.base import Widget


class Slider(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "slider"
        self.qwidget = QSlider()

        self.callables = {
            "set_value": self.set_value,
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False)
        }

        self._setup()

        if "orientation" in self.props:
            self.qwidget.setOrientation(
                Qt.Orientation.Vertical if self.props["orientation"] == "ver"\
                else Qt.Orientation.Horizontal
            )
        else:
            self.qwidget.setOrientation(Qt.Orientation.Horizontal)

        if "max_value" in self.props:
            self.qwidget.setMaximum(self.props["max_value"])

        if "min_value" in self.props:
            self.qwidget.setMinimum(self.props["min_value"])

        self.qwidget.valueChanged.connect(self.vc_handler)

    def vc_handler(self, value: int):

        self._runner.event(
            name=self.name, type="slider_value_changed", value=value
        )

    def set_value(self, data: dict):
        val = data["value"] if "value" in data else 0
        self.qwidget.setValue(val)
