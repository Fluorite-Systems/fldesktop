from PySide6.QtWidgets import QSlider
from PySide6.QtCore import Qt
from fldesktop.include.uikit.widgets.base import Widget


class Slider(Widget):
    def __init__(self, comm, name, attrs):

        self.qwidget = QSlider()

        super().__init__(
            comm, name, attrs,
            {
                "Attr.UI.Widget.Slider.MinValue": 0,
                "Attr.UI.Widget.Slider.MaxValue": 99,
                "Attr.UI.Widget.Slider.Orientation": "hor"
            }
        )

        self.type = "slider"

        self.callables = {
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False)
        }

        self._setup()

        self.qwidget.valueChanged.connect(self.vc_handler)

    def apply_attrs(self):
        super().apply_attrs()

        self.qwidget.setOrientation(
            Qt.Orientation.Vertical if \
                self.attrs["Attr.UI.Widget.Slider.Orientation"] == "ver" \
            else Qt.Orientation.Horizontal
        )

        self.qwidget.setMaximum(self.attrs["Attr.UI.Widget.Slider.MaxValue"])
        self.qwidget.setMinimum(self.attrs["Attr.UI.Widget.Slider.MinValue"])
        
    def vc_handler(self, value: int):

        self.event(type="slider_value_changed", value=value)

