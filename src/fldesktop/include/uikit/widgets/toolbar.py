from PySide6.QtWidgets import QToolBar
from PySide6.QtGui import QPainter, QLinearGradient
from PySide6.QtCore import QPointF
from fldesktop.include.uikit.widgets.base import Widget
from fldesktop.include.thememgr import STD_COLORS


class ColoredToolBar(QToolBar):
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
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


class ToolBar(Widget):
    def __init__(self, comm, name, attrs):
        self.qwidget = QToolBar()
        #self.qwidget.setAutoFillBackground(True)
        super().__init__(comm, name, attrs)
        self.type = "toolbar"

        self._setup()

    def add_child(self, child):

        if hasattr(child, "qwidget"):
            self.qwidget.addWidget(child.qwidget)
            return True