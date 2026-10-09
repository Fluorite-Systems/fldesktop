from PySide6.QtWidgets import QWidget, QSizePolicy

from fldesktop.include.uikit.widgets.base import Widget


class Stretch(Widget):
    def __init__(self, runner, name, attrs):
        super().__init__(runner, name, attrs)
        self.type = "stretch"

        self.qwidget = QWidget()

        self.base_attrs = {
            "Attr.UI.Widget.Stretch.Vertical": True,
            "Attr.UI.Widget.Stretch.Horizontal": True
        }

        self._setup()

    def apply_attrs(self):
        super().apply_attrs()

        if self.attrs["Attr.UI.Widget.Stretch.Vertical"]:
            p1 = QSizePolicy.Policy.Expanding
        else:
            p1 = QSizePolicy.Policy.Fixed

        if self.attrs["Attr.UI.Widget.Stretch.Horizontal"]:
            p2 = QSizePolicy.Policy.Expanding
        else:
            p2 = QSizePolicy.Policy.Fixed

        self.qwidget.setSizePolicy(p2, p1)