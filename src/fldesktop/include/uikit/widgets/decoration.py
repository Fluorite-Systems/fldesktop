from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QLinearGradient, QPainter
from PySide6.QtCore import QPointF

from fldesktop.include.uikit.widgets.base import Widget
from fldesktop.include.thememgr import STD_COLORS


class DecoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._style = "solid"

    def set_style(self, value):
        if value in ["solid", "gradient"]:
            self._style = value
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()

        if self._style == "solid":
            base_color = self.palette().color(self.backgroundRole())

            painter.fillRect(rect, base_color)

        elif self._style == "gradient":
            h = rect.height()
            w = rect.width()

            if h >= w:
                gradient = QLinearGradient(
                    QPointF(0, 0), QPointF(0, h)
                )
            else:
                gradient = QLinearGradient(
                    QPointF(0, 0), QPointF(w, 0)
                )

            gradient.setColorAt(0.0, STD_COLORS["lightcyan"])
            gradient.setColorAt(1.0, STD_COLORS["lightgreen"])

            painter.fillRect(rect, gradient)


class Decoration(Widget):
    def __init__(self, comm, name, attrs):

        self.qwidget = DecoWidget()

        super().__init__(
            comm, name, attrs,
            {"Attr.UI.Widget.Decoration.Style": "solid"}
        )

        self._setup()

    def apply_attrs(self):
        super().apply_attrs()

        self.qwidget.set_style(
            self.attrs["Attr.UI.Widget.Decoration.Style"]
        )