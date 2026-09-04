from PySide6.QtWidgets import (QWidget, QGraphicsScene, QGraphicsPixmapItem,
                               QGraphicsBlurEffect)
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen
from PySide6.QtCore import (Qt, QRect, QObject, QPoint, QTimer,
                            QRandomGenerator)

from fldesktop.include.thememgr import SURFACE_PRESETS
from fldesktop.include.widgets.shadow import Shadow


class Surface(QWidget):
    def __init__(self, comm, parent: QWidget=None, tint: int=1):
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

        self.shadow = Shadow(parent)
        
        # Optimizations
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self._redraw_timer = QTimer(interval=250, singleShot=True)
        self._redraw_timer.timeout.connect(self.update)

        self.comm.subscribe("sfmgr_bg_updated", self._load_background)
        self.comm.subscribe("reload_config", self._update_theming)

        self._load_background()

    def _load_background(self):
        "Request background from surfacemgr"

        self._background = self.comm.request("surfacemgr", "get_pixmap")
        self._invalidate_cache()
        self.update()
    
    def _update_theming(self):
        "Select theming preset from config"

        theme = self.comm.request("cfgmgr", "get", "theme")
        
        self.theme = SURFACE_PRESETS[theme] \
            if theme in SURFACE_PRESETS else SURFACE_PRESETS["neutral"]
    
    def _invalidate_cache(self):
        "Invalidate cached contents"
        
        self._cached = None
        self._cached_pos = None
        self._cached_size = None
    
    def _get_cropped(self) -> QPixmap:
        "Get cropped pixmap from background"

        if not self._background:
            return QPixmap(self.size())
        
        pos_in_window = self.mapToGlobal(QPoint(0, 0))
        
        # Check cache
        if (self._cached is not None and 
            self._cached_pos == pos_in_window and
            self._cached_size == self.size()):
            return self._cached
        
        blurred = QPixmap(self.size())
        blurred.fill(Qt.GlobalColor.black)
        
        widget_rect = QRect(pos_in_window, self.size())
        background_rect = self._background.rect()
        
        intersection = widget_rect.intersected(background_rect)
        
        if not intersection.isEmpty():
            src_x = intersection.x()
            src_y = intersection.y()
            src_width = intersection.width()
            src_height = intersection.height()
            
            dst_x = max(0, -pos_in_window.x())
            dst_y = max(0, -pos_in_window.y())
            
            cropped_from_bg = self._background.copy(
                src_x, src_y, src_width, src_height
            )

            # Tint blurred background for some beauty
            tint = QColor(*self.theme["base_color"],
                    min(255, max(0, self.theme["base_alpha"] + self._tint)))
            
            painter = QPainter(blurred)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, False)
            painter.drawPixmap(dst_x, dst_y, cropped_from_bg)
            painter.fillRect(blurred.rect(), tint)
            painter.end()
        
        # Cache it
        self._cached = blurred
        self._cached_pos = pos_in_window
        self._cached_size = self.size()
        
        return self._cached
    
    def paintEvent(self, event):

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, False)
        cropped = self._get_cropped()
        
        if not cropped.isNull():
            painter.drawPixmap(0, 0, cropped)
        else:
            # Fallback
            painter.fillRect(self.rect(), Qt.GlobalColor.black)

    def update(self):
        self._invalidate_cache()
        super().update()

    def raise_(self):
        self.shadow.raise_()
        super().raise_()

    def lower(self):
        self.shadow.lower()
        super().lower()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._redraw_timer.start()
        self.shadow.resize(event.size())
    
    def moveEvent(self, event):
        super().moveEvent(event)
        self._redraw_timer.start()
        self.shadow.move(event.pos())
    
    def showEvent(self, event):
        super().showEvent(event)
        self.update()
        self.shadow.show()
        self.shadow.raise_()
        self.raise_()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.shadow.hide()

    def closeEvent(self, event):
        self.comm.unsubscribe(self._load_background)
        self.comm.unsubscribe(self._update_theming)
        super().closeEvent(event)


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
            width = rng.bounded(10, 50)
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
