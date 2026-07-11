from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QPoint

from fldesktop.include.compositor.widgets.base import Widget


class Canvas(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "canvas"
        self.qwidget = QWidget()

        self.callables = {
            "resize": self.resize,
            "fill": self.fill,
            "clear": self.clear,
            "draw_line": self.line,
            "draw_rect": self.rect,
            "draw_circle": self.circle,
            #"draw_bezier": self.bezier,
            "draw_text": self.text
        }
        
        self._setup()

        self.pixmap = QPixmap(self.qwidget.width(), self.qwidget.height())
        self.pixmap.fill(Qt.transparent)

        self.qwidget.paintEvent = self.paintEvent

    def resize(self, width: int, height: int):
        
        np = QPixmap(width, height)
        ...
        self.pixmap = np

    def fill(self, color: str):
        self.pixmap.fill(QColor(color))
        self.qwidget.update()
        
    def clear(self):
        self.pixmap.fill(Qt.transparent)
        self.qwidget.update()
        
    def rect(self, x: int, y: int, w: int, h: int,
             outline: str = "#000000", fill: str = "#00000000", 
             width: int = 15):

        painter = QPainter(self.pixmap)
        painter.setPen(QPen(QColor(outline), width))
        painter.setBrush(QColor(fill))
        painter.drawRect(x, y, w, h)
        painter.end()
        self.qwidget.update()
        
    def line(self, x1: int, y1: int, x2: int, y2: int,
             color: str = "#000000", width: int = 15):
        
        painter = QPainter(self.pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(QColor(color), width))
        painter.drawLine(x1, y1, x2, y2)
        painter.end()
        self.qwidget.update()
        
    def circle(self, x: int, y: int, radius: int,
               outline: str = "#000000", fill: str = "#00000000", 
               width: int = 15):

        painter = QPainter(self.pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(QColor(outline), width))
        painter.setBrush(QColor(fill))
        painter.drawEllipse(x - radius, y - radius, 2 * radius, 2 * radius)
        painter.end()
        self.qwidget.update()
        
    def bezier(self, p1, p2, p3, p4, pen=None):
        if isinstance(p1, tuple): p1 = QPointF(*p1)
        if isinstance(p2, tuple): p2 = QPointF(*p2)
        if isinstance(p3, tuple): p3 = QPointF(*p3)
        if isinstance(p4, tuple): p4 = QPointF(*p4)
            
        painter = QPainter(self.pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(pen or self.pen)
        path = QPainterPath()
        path.moveTo(p1)
        path.cubicTo(p2, p3, p4)
        painter.drawPath(path)
        painter.end()
        self.qwidget.update()

    def text(self, text: str, x: int, y: int, size: int, 
             color: str = "white", rotation: int = 0):

        painter = QPainter(self.pixmap)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setPen(QColor(color))
        painter.setFont(QFont("Noto Sans", size))

        if rotation:
            painter.translate(x, y)
            painter.rotate(rotation)

        painter.drawText(x, y, text)
        painter.end()
        self.qwidget.update()
        
    def paintEvent(self, event):
        painter = QPainter(self.qwidget)
        painter.drawPixmap(0, 0, self.pixmap)
