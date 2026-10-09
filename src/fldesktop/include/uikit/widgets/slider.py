from PySide6.QtWidgets import QSlider
from PySide6.QtCore import Qt
from fldesktop.include.uikit.widgets.base import Widget


class Slider(Widget):
    def __init__(self, runner, name, attrs):
        super().__init__(runner, name, attrs)
        self.type = "slider"
        self.qwidget = QSlider()

        self.callables = {
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False)
        }
        
        self.base_attrs = {
            "value": 0,
            "min_value": 0,
            "max_value": 99,
            "orientation": "hor"
        }

        self._setup()

        self.qwidget.valueChanged.connect(self.vc_handler)

    def apply_attrs(self):
        super().apply_attrs()

        self.qwidget.setOrientation(
            Qt.Orientation.Vertical if self.attrs["orientation"] == "ver"\
            else Qt.Orientation.Horizontal
        )

        self.qwidget.setMaximum(self.attrs["max_value"])
        self.qwidget.setMinimum(self.attrs["min_value"])
        
    def vc_handler(self, value: int):

        self._runner.event(
            self,
            name=self.name, type="slider_value_changed", value=value
        )

