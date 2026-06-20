from fldesktop.include.compositor.widgets.base import Widget


class Canvas(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "canvas"

        # Создаём растровый буфер
        self.pixmap = QPixmap(300, 300)
        self.pixmap.fill(Qt.transparent)
        
        # Настройки по умолчанию
        self.pen = QPen(Qt.black, 2, Qt.SolidLine)
        self.brush = QBrush(Qt.NoBrush)
        self.bg_color = Qt.transparent

        self._setup()
    
    def setPen(self, pen):
        """Установить перо для последующих операций."""
        self.pen = pen
        
    def setBrush(self, brush):
        """Установить кисть для заполнения."""
        self.brush = brush
        
    def setBackgroundColor(self, color):
        """Изменить цвет фона (перезаполняет pixmap)."""
        self.bg_color = color
        self.pixmap.fill(color)
        self.update()
        
    def clear(self):
        """Очистить холст (заполнить цветом фона)."""
        self.pixmap.fill(self.bg_color)
        self.update()
        
    def rect(self, x, y, width, height, pen=None, brush=None):
        """Нарисовать прямоугольник."""
        painter = QPainter(self.pixmap)
        painter.setPen(pen or self.pen)
        painter.setBrush(brush or self.brush)
        painter.drawRect(x, y, width, height)
        painter.end()
        self.update()
        
    def line(self, x1, y1, x2, y2, pen=None):
        """Нарисовать линию."""
        painter = QPainter(self.pixmap)
        painter.setPen(pen or self.pen)
        painter.drawLine(x1, y1, x2, y2)
        painter.end()
        self.update()
        
    def circle(self, x, y, radius, pen=None, brush=None):
        """Нарисовать окружность (центр в x,y, радиус radius)."""
        painter = QPainter(self.pixmap)
        painter.setPen(pen or self.pen)
        painter.setBrush(brush or self.brush)
        # drawEllipse принимает верхний левый угол и размеры
        painter.drawEllipse(x - radius, y - radius, 2 * radius, 2 * radius)
        painter.end()
        self.update()
        
    def bezier(self, p1, p2, p3, p4, pen=None):
        """Нарисовать кубическую кривую Безье по 4 точкам."""
        if isinstance(p1, tuple): p1 = QPointF(*p1)
        if isinstance(p2, tuple): p2 = QPointF(*p2)
        if isinstance(p3, tuple): p3 = QPointF(*p3)
        if isinstance(p4, tuple): p4 = QPointF(*p4)
            
        painter = QPainter(self.pixmap)
        painter.setPen(pen or self.pen)
        path = QPainterPath()
        path.moveTo(p1)
        path.cubicTo(p2, p3, p4)
        painter.drawPath(path)
        painter.end()
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pixmap)
