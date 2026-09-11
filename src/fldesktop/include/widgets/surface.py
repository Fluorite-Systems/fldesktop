from PySide6.QtWidgets import (QWidget, QGraphicsScene, QGraphicsPixmapItem,
                               QGraphicsBlurEffect)
from PySide6.QtGui import (QPixmap, QPainter, QColor, QPen, QImage,
                           QRadialGradient)
from PySide6.QtCore import (Qt, QRect, QObject, QPoint, QTimer,
                            QRandomGenerator, QRect, QPointF)

from fldesktop.include.widgets.shadow import Shadow

from dataclasses import dataclass
import numpy as np
import cv2


@dataclass(frozen=True)
class BrightestSpot:
    coords: tuple[int, int]
    max_brightness: float
    relative_brightness: float
    color: QColor
    is_pronounced: bool
    confidence: float


class RayCast:

    def __init__(self):
        self.rays = []
        self.step_size = 2

        angles = np.radians(np.arange(0, 360, 1))
        self._cos_a = np.cos(angles)
        self._sin_a = np.sin(angles)

        self._dx = np.where(np.abs(self._cos_a) > 1e-6, self._cos_a, 1e-6)
        self._dy = np.where(np.abs(self._sin_a) > 1e-6, self._sin_a, 1e-6)

        self._dx_m = self._dx[:, np.newaxis]
        self._dy_m = self._dy[:, np.newaxis]

    def raycast(self, pos: tuple, surfaces):

        valid_surfaces = [s for s in surfaces if getattr(s, "need_raycast", True)]

        if valid_surfaces:
            max_depth = max(valid_surfaces[0].window().width(), valid_surfaces[0].window().height())
        elif surfaces:
            max_depth = max(surfaces[0].window().width(), surfaces[0].window().height())
        else:
            max_depth = 1000.0

        if not valid_surfaces:
            cx = pos[0] + max_depth * self._cos_a
            cy = pos[1] + max_depth * self._sin_a
            return list(zip(cx.astype(int).tolist(), cy.astype(int).tolist(), [max_depth] * 360))

        rects = np.empty((len(valid_surfaces), 4), dtype=np.float32)
        for i, s in enumerate(valid_surfaces):
            gtl = s.mapToGlobal(s.rect().topLeft())
            x, y = gtl.x(), gtl.y()
            rects[i] = (x, x + s.width(), y, y + s.height())

        x, y = pos[0], pos[1]

        t_x1 = (rects[:, 0] - x) / self._dx_m
        t_x2 = (rects[:, 1] - x) / self._dx_m
        t_y1 = (rects[:, 2] - y) / self._dy_m
        t_y2 = (rects[:, 3] - y) / self._dy_m

        t_near = np.maximum(np.minimum(t_x1, t_x2), np.minimum(t_y1, t_y2))
        t_far = np.minimum(np.maximum(t_x1, t_x2), np.maximum(t_y1, t_y2))

        valid_hits = (t_near < t_far) & (t_far > 0) & (t_near < max_depth)

        t_near = np.where(valid_hits, t_near, max_depth)

        closest_t = np.min(t_near, axis=1)

        cx = x + closest_t * self._cos_a
        cy = y + closest_t * self._sin_a

        return list(zip(cx.astype(int).tolist(), cy.astype(int).tolist(), closest_t.tolist()))


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

        self.ray_hits = []
        self.need_raycast = True

        self.shadow = Shadow(parent)
        
        # Optimizations
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self._redraw_timer = QTimer(interval=250, singleShot=True)
        self._redraw_timer.timeout.connect(self.update)

        self.comm.subscribe("sfmgr_bg_updated", self._load_background)
        self.comm.subscribe("reload_config", self._update_theming)
        self.comm.request("surfacemgr", "reg_surface", self)

        self._load_background()

    def _load_background(self):
        "Request background from surfacemgr"

        self._background = self.comm.request("surfacemgr", "get_pixmap")
        self._brightest_spot = self.comm.request("surfacemgr", "get_brightest_spot")
        self._invalidate_cache()
        self.update()

    def _update_theming(self):
        "Load theming configuration"

        self.color = self.comm.request("cfgmgr", "get", "glass-tint-color")
        self.alpha = self.comm.request("cfgmgr", "get", "glass-tint-alpha")
    
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
            tint = QColor(self.color)
            tint.setAlpha(min(255, max(0, self.alpha + self._tint)))

            painter = QPainter(blurred)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, False)

            painter.drawPixmap(dst_x, dst_y, cropped_from_bg)

            # Draw raycasted flares

            RADIUS = 125
            SIZE = RADIUS * 2
            PAD = 30.0

            base_color = QColor(self._brightest_spot.color)

            offset = self.mapToGlobal(QPoint(0, 0))
            ox, oy = offset.x(), offset.y()

            w_width = float(self.width())
            w_height = float(self.height())
            max_depth = float(max(self.window().width(), self.window().height()))

            painter.setRenderHint(QPainter.Antialiasing)
            painter.setCompositionMode(QPainter.CompositionMode_Screen)
            painter.setOpacity(1.0) 

            painter.setClipRect(0, 0, int(w_width), int(w_height))

            last_drawn_x = -9999.0
            last_drawn_y = -9999.0
            MIN_SPACING_SQ = 12.0 ** 2  

            for hit in self.comm.request("surfacemgr", "get_hits"):
                x = hit[0] - ox
                y = hit[1] - oy

                if not (-PAD <= x <= w_width + PAD and -PAD <= y <= w_height + PAD):
                    continue

                dist_sq = (x - last_drawn_x) ** 2 + (y - last_drawn_y) ** 2

                if dist_sq >= MIN_SPACING_SQ or last_drawn_x == -9999.0:
                    length = hit[2]
                    
                    factor = max(0.0, min(1.0, 1.0 - (length / max_depth)))
                    current_alpha = int(25 * factor)
                    
                    if current_alpha > 0:
                        center_pt = QPointF(x, y)
                        grad = QRadialGradient(center_pt, float(RADIUS))
                        
                        color_center = QColor(base_color)
                        color_center.setAlpha(current_alpha)
                        
                        grad.setColorAt(0.0, color_center)
                        grad.setColorAt(1.0, Qt.transparent)
                        
                        painter.fillRect(QRect(x - RADIUS, y - RADIUS, SIZE, SIZE), grad)
                    
                    last_drawn_x = x
                    last_drawn_y = y

            painter.setOpacity(1.0)

            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
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

    def set_raycast_enabled(self, enable: bool):

        self.need_raycast = enable
        self.comm.request("surfacemgr", "raycast")

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
        self.shadow.resize(event.size())
        self.comm.request("surfacemgr", "raycast")
    
    def moveEvent(self, event):
        super().moveEvent(event)
        self.shadow.move(event.pos())
        self.comm.request("surfacemgr", "raycast")
    
    def showEvent(self, event):
        super().showEvent(event)
        self.update()
        self.shadow.show()
        self.shadow.raise_()
        self.raise_()
        self.comm.request("surfacemgr", "raycast")
        self.need_raycast = True

    def hideEvent(self, event):
        super().hideEvent(event)
        self.shadow.hide()
        self.comm.request("surfacemgr", "raycast")
        self.need_raycast = False

    def closeEvent(self, event):
        self.comm.unsubscribe(self._load_background)
        self.comm.unsubscribe(self._update_theming)
        self.comm.request("surfacemgr", "unreg_surface", self)
        super().closeEvent(event)


class SurfaceManager(QObject):
    def __init__(self, comm):
        super().__init__()

        self.comm = comm

        self.comm.register(
            "surfacemgr", {
                "refresh": self.refresh,
                "get_pixmap": self.get_pixmap,
                "get_brightest_spot": self.get_brightest_spot,
                "get_hits": self.get_hits,
                "reg_surface": self.reg_surface,
                "unreg_surface": self.unreg_surface,
                "raycast": self.do_raycast
            }
        )

        self.brightest_spot = BrightestSpot((0, 0), 0, 0, QColor(), False, 0)

        self.blur_radius = 80

        self.pixmap = QPixmap()

        self.surfaces = []
        self.hits = []
        self.raycast_enabled = True
        self.rc = RayCast()

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

        # Find the brightest spot

        self.brightest_spot = self.find_brightest_spot(pixmap)
        
        # Draw some lines

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rng = QRandomGenerator()
    
        height = pixmap.height()
        width_total = pixmap.width()
        
        x = -height
        
        while x < width_total + height:
            width = rng.bounded(10, 50)
            alpha = rng.bounded(0, 120)
            
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

    def find_brightest_spot(self, pixmap: QPixmap) -> BrightestSpot:

        if pixmap is None or pixmap.isNull() or pixmap.width() <= 0 or pixmap.height() <= 0:
            return BrightestSpot((0, 0), 0.0, 0.0, QColor(0, 0, 0), is_pronounced=False, confidence=0.0)

        w, h = pixmap.width(), pixmap.height()

        image = pixmap.toImage().convertToFormat(QImage.Format.Format_RGB888)
        
        buffer = image.bits()
        
        img_array = np.array(buffer, dtype=np.uint8).reshape((h, w, 3)).copy()

        r = img_array[:, :, 0].astype(np.float32)
        g = img_array[:, :, 1].astype(np.float32)
        b = img_array[:, :, 2].astype(np.float32)
        gray_f = 0.299 * r + 0.587 * g + 0.114 * b
        gray = gray_f.astype(np.uint8)
        
        ambient_brightness = float(np.mean(gray))
        std_deviation = float(np.std(gray))

        _, thresh = cv2.threshold(gray, 225, 255, cv2.THRESH_BINARY)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(thresh)
        
        best_label = -1
        best_score = -1

        if num_labels > 1:
            for i in range(1, num_labels):
                area = stats[i, cv2.CC_STAT_AREA]

                if area < 4:
                    continue
                    
                mask = (labels == i)
                mean_val = cv2.mean(gray, mask=mask.astype(np.uint8))[0]
                
                score = area * (mean_val ** 2)
                
                if score > best_score:
                    best_score = score
                    best_label = i

        if best_label == -1:
            max_idx = np.argmax(gray)
            center_y, center_x = np.unravel_index(max_idx, gray.shape)
            target_area = 1
        else:
            target_area = stats[best_label, cv2.CC_STAT_AREA]
            target_mask = (labels == best_label)
            masked_gray = np.zeros_like(gray)
            masked_gray[target_mask] = gray[target_mask]
            max_idx = np.argmax(masked_gray)
            center_y, center_x = np.unravel_index(max_idx, gray.shape)

        max_brightness = float(gray[center_y, center_x])
        relative_brightness = max_brightness - ambient_brightness

        if std_deviation < 5.0:
            confidence = 0.0
        else:
            contrast_factor = relative_brightness / (std_deviation + 1e-5)
            area_factor = target_area / (w * h)
            confidence = contrast_factor * (1.0 + np.log1p(area_factor * 3000))

        is_light_source = (
            confidence > 3.5 and 
            max_brightness >= 235.0 and 
            relative_brightness > 45.0
        )

        is_pronounced = bool(is_light_source)

        threshold = max_brightness * 0.92
        row_center = gray[center_y, :]
        core_pixels_x = np.where(row_center > threshold)[0]
        col_center = gray[:, center_x]
        core_pixels_y = np.where(col_center > threshold)[0]
        
        core_width = (core_pixels_x[-1] - core_pixels_x[0]) if len(core_pixels_x) > 0 else 1
        core_height = (core_pixels_y[-1] - core_pixels_y[0]) if len(core_pixels_y) > 0 else 1
        core_radius = max(core_width, core_height) // 2
        
        search_radius = int(core_radius * 1.5)
        min_allowed_radius = max(8, int(min(w, h) * 0.015))
        max_allowed_radius = int(min(w, h) * 0.12)
        search_radius = max(min_allowed_radius, min(search_radius, max_allowed_radius))

        y_min = max(0, center_y - search_radius)
        y_max = min(h, center_y + search_radius + 1)
        x_min = max(0, center_x - search_radius)
        x_max = min(w, center_x + search_radius + 1)

        best_color = QColor(int(img_array[center_y, center_x, 0]), 
                            int(img_array[center_y, center_x, 1]), 
                            int(img_array[center_y, center_x, 2]))
        max_saturation = -1

        y_indices, x_indices = np.ogrid[y_min:y_max, x_min:x_max]
        inside_circle = (x_indices - center_x) ** 2 + (y_indices - center_y) ** 2 <= search_radius ** 2
        sub_array = img_array[y_min:y_max, x_min:x_max]
        
        for y_idx in range(sub_array.shape[0]):
            for x_idx in range(sub_array.shape[1]):
                if inside_circle[y_idx, x_idx]:
                    current_color = QColor(int(sub_array[y_idx, x_idx, 0]), 
                                        int(sub_array[y_idx, x_idx, 1]), 
                                        int(sub_array[y_idx, x_idx, 2]))
                    saturation = current_color.hsvSaturation()
                    if saturation > max_saturation:
                        max_saturation = saturation
                        best_color = current_color

        return BrightestSpot(
            coords=(int(center_x), int(center_y)),
            max_brightness=max_brightness,
            relative_brightness=relative_brightness,
            color=best_color,
            is_pronounced=is_pronounced,
            confidence=float(confidence)
        )

    def reg_surface(self, surface):

        self.surfaces.append(surface)

    def unreg_surface(self, surface):

        self.surfaces.remove(surface)

    def do_raycast(self):

        need_raycast = self.brightest_spot.is_pronounced

        for s in self.surfaces:
            pos = s.pos()
            size = s.size()

            if s.need_raycast:

                bx, by = self.brightest_spot.coords
                
                px, py = float(pos.x()), float(pos.y())
                pw, ph = float(size.width()), float(size.height())
                
                if px <= bx <= px + pw and py <= by <= py + ph:
                    need_raycast = False

        if need_raycast:
            self.hits = self.rc.raycast(self.brightest_spot.coords, self.surfaces)
        else:
            self.hits = []
        
        for s in self.surfaces:
            s.update()
    
    def get_pixmap(self):
        return self.pixmap

    def get_brightest_spot(self):
        return self.brightest_spot

    def get_hits(self):
        return self.hits