import time
from pathlib import Path

from PySide6.QtCore import QEvent, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication, QWidget

from fldesktop.include.superfx.container import (
    GlassConfig, PROP_LAYER, PROP_LAYER_LOCKED, PROP_CONTENT_STATIC,
    PROP_TINT_SCALE, PROP_TINT_COLOR, PROP_OPACITY,
    _alive, _prop, _app_closing, _paintable, _coerce_layer,
)
from fldesktop.include.superfx.glrender import (
    _Reg,
    SHOW_FPS,
    FPS_REFRESH_S,
    SAFETY_INTERVAL_MS,
)


SHADOW_T, SHADOW_R, SHADOW_B, SHADOW_L = 25, 31, 33, 26


class SimpleRender(QWidget):
    def __init__(self, parent, config=None):
        super().__init__(parent)
        if config is None:
            config = GlassConfig()
        self.config = config

        self.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(
            Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(
            Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self._regs = []
        self._reg_by_widget = {}

        self._wallpaper_image = None
        self._shadow_image = None

        self._shutting_down = False
        self._update_pending = False

        self._frames = 0
        self._fps_t = time.perf_counter()
        self._fps = 0.0

        self._safety = QTimer(self)
        self._safety.setTimerType(Qt.TimerType.VeryCoarseTimer)
        self._safety.setInterval(SAFETY_INTERVAL_MS)
        self._safety.timeout.connect(self._on_safety_tick)
        self._safety.start()

        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)

    def _request_frame(self):
        if self._update_pending:
            return
        if _app_closing() or self._shutting_down:
            return
        self._update_pending = True
        try:
            self.update()
        except (RuntimeError, SystemError):
            self._update_pending = False

    def _mark_dirty(self, r):
        if r is None:
            return
        r.dirty = True
        self._request_frame()

    def _tick_surfaces(self):
        animating = False
        for r in self._regs:
            w = r.widget
            if not _alive(w):
                continue
            fn = getattr(w, "invoke_update", None)
            if not callable(fn):
                continue
            try:
                if fn() and _paintable(w):
                    r.dirty = True
                    animating = True
            except Exception:
                pass
        return animating

    def _on_safety_tick(self):
        if _app_closing() or self._shutting_down:
            try:
                self._safety.stop()
            except (RuntimeError, SystemError):
                pass
            return
        if self._update_pending:
            return
        self._tick_surfaces()
        if any(r.dirty for r in self._regs
               if _alive(r.widget) and _paintable(r.widget)):
            self._request_frame()

    def _install_update_hook(self, w):
        if getattr(w, "_compositor_hooked", False):
            return
        try:
            original = w.update
        except (RuntimeError, SystemError):
            return

        owner = self

        def _hook(*args, __w=w, __o=original, **kwargs):
            try:
                r = owner._reg_by_widget.get(__w)
            except (RuntimeError, SystemError):
                r = None
            if r is not None and not r._rendering:
                r.dirty = True
                owner._request_frame()
            return __o(*args, **kwargs)

        try:
            w.update = _hook
            w._compositor_hooked = True
        except (RuntimeError, SystemError):
            return

        try:
            for child in w.findChildren(QWidget):
                self._install_update_hook(child)
        except (RuntimeError, SystemError):
            pass

    def _uninstall_update_hook(self, w):
        if getattr(w, "_compositor_hooked", False):
            try:
                del w.update
                del w._compositor_hooked
            except (AttributeError, TypeError):
                pass
        try:
            for child in w.findChildren(QWidget):
                self._uninstall_update_hook(child)
        except (RuntimeError, SystemError):
            pass

    def set_wallpaper(self, image):
        self._wallpaper_image = image
        self._request_frame()

    def register(self, widget, z=1.0, glass=True,
                 layer=None, locked=None):
        for r in self._regs:
            if r.widget is widget:
                return r

        if layer is None:
            layer = _coerce_layer(_prop(widget, PROP_LAYER))
        else:
            layer = _coerce_layer(layer)

        if locked is None:
            locked = bool(_prop(widget, PROP_LAYER_LOCKED))
        else:
            locked = bool(locked)

        r = _Reg(widget, z, glass, layer, locked)
        self._regs.append(r)
        self._regs.sort(key=lambda x: (x.layer, x.z))
        self._reg_by_widget[widget] = r
        self._apply_dont_show(r, True)
        self._install_update_hook(widget)
        self._request_frame()
        return r

    def unregister(self, widget):
        for r in self._regs:
            if r.widget is widget:
                self._regs.remove(r)
                self._reg_by_widget.pop(widget, None)
                self._uninstall_update_hook(widget)
                r.img = None
                self._request_frame()
                return True
        return False

    def raise_surface(self, widget):
        r = self._reg_by_widget.get(widget)
        if r is None or r.locked:
            return
        peers = [x for x in self._regs
                 if x is not r and x.layer == r.layer]
        if not peers:
            return
        top = max(x.z for x in peers)
        if r.z > top:
            return
        r.z = top + 1.0
        self._regs.sort(key=lambda x: (x.layer, x.z))
        self._request_frame()

    def lower_surface(self, widget):
        r = self._reg_by_widget.get(widget)
        if r is None or r.locked:
            return
        peers = [x for x in self._regs
                 if x is not r and x.layer == r.layer]
        if not peers:
            return
        r.z = min(x.z for x in peers) - 1.0
        self._regs.sort(key=lambda x: (x.layer, x.z))
        self._request_frame()

    def invalidate(self, widget=None):
        if widget is None:
            for r in self._regs:
                r.dirty = True
        else:
            r = self._reg_by_widget.get(widget)
            if r is not None:
                r.dirty = True
        self._request_frame()

    def force_refresh(self, widget):
        r = self._reg_by_widget.get(widget)
        if r is not None:
            r.dirty = True
            self._request_frame()

    def eventFilter(self, obj, ev):
        if not isinstance(obj, QWidget):
            return False
        if _app_closing() or self._shutting_down:
            return False
        et = ev.type()

        if et == QEvent.Type.Move:
            return False

        if et not in (QEvent.Type.UpdateRequest,
                      QEvent.Type.Resize,
                      QEvent.Type.Show,
                      QEvent.Type.Hide,
                      QEvent.Type.Paint):
            return False

        r = self._reg_by_widget.get(obj)
        if r is None:
            r = self._reg_of(obj)
        if r is None:
            return False

        if r._rendering:
            return False

        if et == QEvent.Type.Paint:
            self._mark_dirty(r)
            return False

        if _prop(r.widget, PROP_CONTENT_STATIC) is True:
            if r.img is not None and et != QEvent.Type.Show:
                return False

        self._mark_dirty(r)
        return False

    def _reg_of(self, w):
        while w is not None:
            r = self._reg_by_widget.get(w)
            if r is not None:
                return r
            try:
                w = w.parentWidget()
            except (RuntimeError, SystemError):
                return None
        return None

    def initializeGL(self):
        pass

    def resizeGL(self, w, h):
        pass

    def closeEvent(self, ev):
        self._shutting_down = True

        try:
            self._safety.stop()
        except (RuntimeError, SystemError):
            pass

        app = QApplication.instance()
        if app is not None:
            try:
                app.removeEventFilter(self)
            except (RuntimeError, SystemError):
                pass

        for r in self._regs:
            if _alive(r.widget):
                self._uninstall_update_hook(r.widget)

        for r in self._regs:
            r.widget = None
            r.img = None
        self._regs.clear()
        self._reg_by_widget.clear()
        self._wallpaper_image = None
        self._shadow_image = None

        super().closeEvent(ev)

    def _apply_dont_show(self, r, on):
        w = r.widget
        if not _alive(w):
            return
        if r._dont_show_applied == bool(on):
            return
        try:
            w.setAttribute(
                Qt.WidgetAttribute.WA_DontShowOnScreen, bool(on))
            r._dont_show_applied = bool(on)
        except (RuntimeError, SystemError):
            pass

    def _refresh_surface_img(self, r):
        w = r.widget
        if not _alive(w):
            return
        ww, wh = w.width(), w.height()
        if ww <= 0 or wh <= 0:
            return

        fmt = QImage.Format.Format_RGBA8888_Premultiplied
        if (r.img is None
                or r.img.width() != ww
                or r.img.height() != wh):
            r.img = QImage(ww, wh, fmt)
        r.img.fill(0)

        r._rendering = True
        try:
            w.render(r.img)
            r.dirty = False
        except (RuntimeError, SystemError):
            pass
        finally:
            r._rendering = False

    def _collect_visible(self):
        visible = []
        for r in self._regs:
            w = r.widget
            if not _alive(w):
                continue
            if not w.isVisible():
                continue
            if not _paintable(w):
                continue
            if w.width() <= 0 or w.height() <= 0:
                continue
            if r.layer == 0.0 and self._wallpaper_image is not None:
                continue
            visible.append(r)
        return visible

    def _tint_scale(self, w):
        v = _prop(w, PROP_TINT_SCALE)
        if v is None:
            return 1.0
        try:
            return float(v)
        except (TypeError, ValueError):
            return 1.0

    def _tint_color(self, w):
        v = _prop(w, PROP_TINT_COLOR)
        if v is None:
            return (1.0, 1.0, 1.0)
        try:
            if len(v) == 3:
                return (float(v[0]), float(v[1]), float(v[2]))
        except (TypeError, ValueError, IndexError):
            pass
        return (1.0, 1.0, 1.0)

    def _opacity(self, w):
        v = _prop(w, PROP_OPACITY)
        if v is None:
            return 1.0
        try:
            return max(0.0, min(1.0, float(v)))
        except (TypeError, ValueError):
            return 1.0

    def _ensure_shadow_image(self):
        if self._shadow_image is not None:
            return self._shadow_image
        path = (Path(__file__).resolve().parent.parent
                / "assets" / "shadow.png")
        if not path.exists():
            self._shadow_image = QImage()
            return self._shadow_image
        self._shadow_image = QImage(str(path))
        return self._shadow_image

    def _draw_shadow(self, painter, x, y, ww, wh, opacity):
        img = self._ensure_shadow_image()
        if img.isNull():
            return

        alpha = float(self.config.shadow_alpha) * opacity
        if alpha <= 0.0:
            return

        t, r, b, l = SHADOW_T, SHADOW_R, SHADOW_B, SHADOW_L
        iw, ih = img.width(), img.height()
        if iw <= l + r or ih <= t + b:
            return

        dx = x - l
        dy = y - t
        dw = ww + l + r
        dh = wh + t + b
        sw = iw - l - r
        sh = ih - t - b
        mw = dw - l - r
        mh = dh - t - b

        painter.save()
        painter.setOpacity(alpha)

        painter.drawImage(QRectF(dx, dy, l, t),
                          img, QRectF(0, 0, l, t))
        painter.drawImage(QRectF(dx + dw - r, dy, r, t),
                          img, QRectF(iw - r, 0, r, t))
        painter.drawImage(QRectF(dx, dy + dh - b, l, b),
                          img, QRectF(0, ih - b, l, b))
        painter.drawImage(QRectF(dx + dw - r, dy + dh - b, r, b),
                          img, QRectF(iw - r, ih - b, r, b))

        painter.drawImage(QRectF(dx + l, dy, mw, t),
                          img, QRectF(l, 0, sw, t))
        painter.drawImage(QRectF(dx + l, dy + dh - b, mw, b),
                          img, QRectF(l, ih - b, sw, b))
        painter.drawImage(QRectF(dx, dy + t, l, mh),
                          img, QRectF(0, t, l, sh))
        painter.drawImage(QRectF(dx + dw - r, dy + t, r, mh),
                          img, QRectF(iw - r, t, r, sh))

        painter.drawImage(QRectF(dx + l, dy + t, mw, mh),
                          img, QRectF(l, t, sw, sh))

        painter.restore()

    def paintEvent(self, ev):
        if self._shutting_down or _app_closing():
            return

        self._update_pending = False

        animating = self._tick_surfaces()

        try:
            self._paint()
        except Exception:
            pass

        still_dirty = any(
            r.dirty for r in self._regs
            if _alive(r.widget) and _paintable(r.widget))

        if animating or still_dirty:
            self._request_frame()

    def _paint(self):
        W, H = self.width(), self.height()
        if W <= 0 or H <= 0:
            return

        painter = QPainter(self)
        try:
            painter.setRenderHint(
                QPainter.RenderHint.Antialiasing, True)
            painter.setRenderHint(
                QPainter.RenderHint.SmoothPixmapTransform, True)

            if self._wallpaper_image is not None:
                wi = self._wallpaper_image
                if wi.width() > 0 and wi.height() > 0:
                    scaled = wi.scaled(
                        W, H,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation)
                    sx = max(0, (scaled.width() - W) // 2)
                    sy = max(0, (scaled.height() - H) // 2)
                    painter.drawImage(
                        QRectF(0, 0, W, H), scaled,
                        QRectF(sx, sy, W, H))
                else:
                    painter.fillRect(self.rect(), QColor(5, 5, 8))
            else:
                painter.fillRect(self.rect(), QColor(5, 5, 8))

            for r in self._collect_visible():
                self._paint_window(painter, r, W, H)
        finally:
            painter.end()

        self._frames += 1
        now = time.perf_counter()
        if now - self._fps_t >= FPS_REFRESH_S:
            self._fps = self._frames / (now - self._fps_t)
            self._frames = 0
            self._fps_t = now
            win = self.window()
            if SHOW_FPS and win is not None and win is not self:
                base = (getattr(win, "_base_title", None)
                        or win.windowTitle())
                win._base_title = base
                win.setWindowTitle(f"{base} — {self._fps:.0f} FPS")

    def _paint_window(self, painter, r, W, H):
        w = r.widget
        if not _alive(w):
            return
        x, y, ww, wh = r.geom
        if ww <= 0 or wh <= 0:
            return

        if (r.img is None
                or r.img.width() != ww
                or r.img.height() != wh
                or r.dirty):
            self._refresh_surface_img(r)

        opacity = self._opacity(w)
        tint_scale = self._tint_scale(w)
        tint_override = self._tint_color(w)

        self._draw_shadow(painter, x, y, ww, wh, opacity)

        if r.glass:
            tr, tg, tb = self.config.tint
            tr = max(0.0, min(1.0, float(tr) * tint_override[0]))
            tg = max(0.0, min(1.0, float(tg) * tint_override[1]))
            tb = max(0.0, min(1.0, float(tb) * tint_override[2]))
            strength = (float(self.config.tint_amount) * 1.5
                        * tint_scale * opacity)
            a = int(max(0.0, min(1.0, strength)) * 255)
            if a > 0:
                bg = QColor(
                    int(tr * 255), int(tg * 255), int(tb * 255), a)
                painter.save()
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(bg)
                painter.drawRect(QRectF(x, y, ww, wh))
                painter.restore()

        if r.img is not None and not r.img.isNull():
            painter.save()
            painter.setOpacity(opacity)
            painter.drawImage(x, y, r.img)
            painter.restore()