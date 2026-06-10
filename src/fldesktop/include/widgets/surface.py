from PySide6.QtWidgets import (QWidget, QGraphicsScene, QGraphicsPixmapItem,
                               QGraphicsBlurEffect)
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen
from PySide6.QtCore import (Qt, QRect, QObject, QPoint, QTimer,
                            QRandomGenerator)

from fldesktop.include.thememgr import SURFACE_PRESETS


class Surface(QWidget):
    def __init__(self, comm, parent=None, tint: int=1):
        super().__init__(parent)
        self.comm = comm
        self._background = None
        self._cached = None
        self._cached_pos = None
        self._cached_size = None
        self._tint = 255 // (10 - tint)

        if self._tint < 0:
            self._tint = 0

        self._update_theming()
        
        # Оптимизация отрисовки
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self._redraw_timer = QTimer(interval=250, singleShot=True)
        self._redraw_timer.timeout.connect(self.update)

        self.comm.subscribe("sfmgr_bg_updated", self._load_background)
        self.comm.subscribe("reload_config", self._update_theming)

        self._load_background()

    def _load_background(self):
        """Загружает фон из comm"""
        self._background = self.comm.request("surfacemgr", "get_pixmap")
        self._invalidate_cache()
        self.update()
    
    def _update_theming(self):
        theme = self.comm.request("cfgmgr", "get", "theme")
        
        self.theme = SURFACE_PRESETS[theme] \
            if theme in SURFACE_PRESETS else SURFACE_PRESETS["neutral"]
    
    def _invalidate_cache(self):
        """Сбрасывает кэш"""
        self._cached = None
        self._cached_pos = None
        self._cached_size = None
    
    def _get_cropped(self) -> QPixmap:
        """Вырезает нужную область с учетом отрицательных координат и выходов за границы"""
        if not self._background:
            return QPixmap(self.size())
        
        # Получаем позицию виджета относительно окна
        pos_in_window = self.mapToGlobal(QPoint(0, 0))
        
        # Проверяем кэш (учитываем позицию и размер)
        if (self._cached is not None and 
            self._cached_pos == pos_in_window and
            self._cached_size == self.size()):
            return self._cached
        
        # Создаем результирующий pixmap с черным фоном
        blurred = QPixmap(self.size())
        blurred.fill(Qt.GlobalColor.black)
        
        # Вычисляем область пересечения виджета с фоном
        # Виджет может быть частично за пределами фона (отрицательные координаты)
        widget_rect = QRect(pos_in_window, self.size())
        background_rect = self._background.rect()
        
        # Находим пересечение
        intersection = widget_rect.intersected(background_rect)
        
        if not intersection.isEmpty():
            # Вырезаем из фона ту часть, которая попадает в виджет
            # Относительные координаты в фоне
            src_x = intersection.x()
            src_y = intersection.y()
            src_width = intersection.width()
            src_height = intersection.height()
            
            # Куда рисовать в виджете
            # Если виджет находится левее/выше фона, то часть виджета не попадает в фон
            dst_x = max(0, -pos_in_window.x())
            dst_y = max(0, -pos_in_window.y())
            
            # Вырезаем нужную часть из фона
            cropped_from_bg = self._background.copy(
                src_x, src_y, src_width, src_height
            )

            tint = QColor(*self.theme["base_color"],
                    min(255, max(0, self.theme["base_alpha"] + self._tint)))
            
            # Рисуем на результат
            painter = QPainter(blurred)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, False)
            painter.drawPixmap(dst_x, dst_y, cropped_from_bg)
            painter.fillRect(blurred.rect(), tint)
            painter.end()
        
        # Сохраняем в кэш
        self._cached = blurred
        self._cached_pos = pos_in_window
        self._cached_size = self.size()
        
        return self._cached
    
    def paintEvent(self, event):
        """Отрисовка виджета"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, False)
        cropped = self._get_cropped()
        
        if not cropped.isNull():
            painter.drawPixmap(0, 0, cropped)
        else:
            # Fallback - если что-то пошло не так
            painter.fillRect(self.rect(), Qt.GlobalColor.black)
    
    def update(self):
        self._invalidate_cache()
        super().update()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._redraw_timer.start()
    
    def moveEvent(self, event):
        super().moveEvent(event)
        self._redraw_timer.start()
    
    def showEvent(self, event):
        super().showEvent(event)
        self.update()


class SurfaceManager(QObject):
    def __init__(self, comm):
        super().__init__()

        self.comm = comm

        self.comm.register(
            "surfacemgr", {
                "refresh": self.refresh,
                "get_pixmap": self.get_pixmap
            }
        )

        self.blur_radius = 80

        self.pixmap = QPixmap()

        self.refresh()

    def refresh(self):
        "Update blurred background"

        desktop = self.comm.request("desktop", "get_instance")

        if desktop:
            pixmap = desktop.bg.grab()
        else:
            pixmap = QPixmap()
            pixmap.fill(Qt.GlobalColor.darkCyan)

        if pixmap.isNull():
            return QPixmap()
        
        # Draw some lines

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rng = QRandomGenerator()
    
        height = pixmap.height()
        width_total = pixmap.width()
        
        x = -height
        
        while x < width_total + height:
            width = rng.bounded(30, 80)
            alpha = rng.bounded(0, 70)
            
            if alpha >= 20:
                pen = QPen(QColor(0, 0, 0, alpha))
                pen.setWidth(width)
                painter.setPen(pen)
                painter.drawLine(x, 0, x + height, height)
            
            step = width - rng.bounded(5, 15)
            x += step
        
        painter.end()

        # Add blur

        scene = QGraphicsScene()

        pixmap_item = QGraphicsPixmapItem(pixmap)
        scene.addItem(pixmap_item)

        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurHints(QGraphicsBlurEffect.BlurHint.QualityHint)
        blur_effect.setBlurRadius(self.blur_radius)
        pixmap_item.setGraphicsEffect(blur_effect)

        scene.setSceneRect(pixmap.rect())

        blurred = QPixmap(pixmap.size())
        blurred.fill(Qt.transparent)

        painter = QPainter(blurred)
        scene.render(painter, pixmap.rect(), pixmap.rect())
        painter.end()

        self.pixmap = blurred

        self.comm.emit("sfmgr_bg_updated")
    
    def get_pixmap(self):
        return self.pixmap