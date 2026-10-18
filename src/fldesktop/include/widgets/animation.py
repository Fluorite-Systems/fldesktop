import time

from PySide6.QtCore import QPoint, QSize, QRect, Qt, QObject
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtWidgets import QWidget

from fldesktop.include.widgets.surface import Surface
from fldesktop.include.superfx.glrender import PROP_OPACITY


def _out_quart(t):
    u = 1.0 - t
    return 1.0 - u * u * u * u


from PySide6.QtCore import QRect

def _lerp(a, b, t):
    if isinstance(a, QPoint):
        return QPoint(
            int(a.x() + (b.x() - a.x()) * t),
            int(a.y() + (b.y() - a.y()) * t))
    if isinstance(a, QSize):
        return QSize(
            int(a.width() + (b.width() - a.width()) * t),
            int(a.height() + (b.height() - a.height()) * t))
    if isinstance(a, QRect):
        return QRect(
            int(a.x() + (b.x() - a.x()) * t),
            int(a.y() + (b.y() - a.y()) * t),
            int(a.width() + (b.width() - a.width()) * t),
            int(a.height() + (b.height() - a.height()) * t))
    return a + (b - a) * t


class Animator(QObject):
    def __init__(self, widget, prop, start, end, duration_ms,
                 on_finished=None, parent=None):
        super().__init__(parent if parent is not None else widget)
        self._w = widget
        self._prop = prop
        self._start = start
        self._end = end
        self._duration_ms = int(duration_ms)
        self._on_finished = on_finished
        self._running = self._duration_ms > 0
        self._start_t = time.perf_counter()
        self._end_t = self._start_t + self._duration_ms / 1000.0
        self._last = start
        self._apply(start)
        if not self._running:
            self._finish_now()

    def _apply(self, value):
        w = self._w
        if self._prop == "pos":
            w.move(value)
        elif self._prop == "size":
            w.resize(value)
        elif self._prop == "geometry":
            w.setGeometry(value)
        elif self._prop == PROP_OPACITY:
            w.setProperty(PROP_OPACITY, float(value))
        else:
            setattr(w, self._prop, value)

    def _read(self):
        if self._prop == "pos":
            return self._w.pos()
        if self._prop == "size":
            return self._w.size()
        if self._prop == "geometry":
            g = self._w.geometry()
            return (g.x(), g.y(), g.size())
        if self._prop == PROP_OPACITY:
            v = self._w.property(PROP_OPACITY)
            return 1.0 if v is None else float(v)
        return getattr(self._w, self._prop)

    def invoke_update(self):
        if not self._running:
            return False
        now = time.perf_counter()
        if now >= self._end_t:
            self._apply(self._end)
            self._last = self._end
            self._running = False
            self._finish_now()
            return True
        t = (now - self._start_t) / (self._end_t - self._start_t)
        value = _lerp(self._start, self._end, _out_quart(t))
        if value != self._last:
            self._last = value
            self._apply(value)
            return True
        return False

    def _finish_now(self):
        cb = self._on_finished
        self._on_finished = None
        if callable(cb):
            try:
                cb()
            except Exception:
                pass
        self.deleteLater()


class Animation(Surface):
    def __init__(self, comm, parent: QWidget, pixmap: QPixmap,
                 type: str, params: dict, on_finished):
        super().__init__(
            comm, never_materialize=True, layer=3,
            tint_color=params["tint_color"]
                if "tint_color" in params else None,
            tint_alpha=params["tint_alpha"]
                if "tint_alpha" in params else None
        )

        self.setAttribute(Qt.WA_DeleteOnClose)

        self.pixmap = pixmap
        self.comm = comm
        self._on_finished = on_finished
        self._animators = []

        self.show()
        self.raise_()

        if not comm.request("lockscreen", "is_visible"):
            comm.request("panel", "raise")

        if "glow_enabled" in params:
            if not params["glow_enabled"]:
                self.set_glow_enabled(False)

        self.animate(type, params, on_finished)

    def _set_instant(self, prop, value):
        if prop == "pos":
            self.move(value)
        elif prop == "size":
            self.resize(value)
        elif prop == "geometry":
            self.setGeometry(value[0], value[1],
                             value[2].width(), value[2].height())
        elif prop == PROP_OPACITY:
            self.setProperty(PROP_OPACITY, float(value))
        else:
            setattr(self, prop, value)

    def _add_animator(self, prop, start, end, duration_ms):
        a = Animator(self, prop, start, end, duration_ms,
                     on_finished=self._maybe_finish)
        self._animators.append(a)
        return a

    def animate(self, type: str, params: dict, on_finished):
        self._on_finished = on_finished
        pos = params["pos"] if "pos" in params else QPoint()
        size = params["size"] if "size" in params else QSize()

        match type:
            case "wmaximize":
                self._set_instant(PROP_OPACITY, 1.0)
                self._add_animator("pos",
                    QPoint(pos.x() + 50, pos.y() + 50), pos, 150)
                self._add_animator("size",
                    QSize(size.width() - 100, size.height() - 100),
                    size, 150)
                return

            case "wunmaximize":
                self._set_instant(PROP_OPACITY, 1.0)
                self._add_animator("pos",
                    QPoint(pos.x() - 50, pos.y() - 50), pos, 150)
                self._add_animator("size",
                    QSize(size.width() + 100, size.height() + 100),
                    size, 150)
                return

            case "wminimize":
                self._add_animator("pos", pos,
                    QPoint(pos.x() // 2, pos.y() // 2), 150)
                self._add_animator("size", size, QSize(0, 0), 150)
                self._add_animator(PROP_OPACITY, 1.0, 0.0, 150)
                return

            case "wunminimize":
                self._add_animator("pos",
                    QPoint(pos.x() - 100, pos.y() - 100), pos, 150)
                self._add_animator("size",
                    QSize(size.width() - 100, size.height() - 100),
                    size, 150)
                self._add_animator(PROP_OPACITY, 0.0, 1.0, 150)
                return

            case "wopen":
                self._add_animator("pos",
                    QPoint(pos.x() + size.width() // 4, pos.y() + size.height() // 4),
                    pos, 250)
                self._add_animator("size",
                    QSize(size.width() // 2, size.height() // 2), size, 250)
                self._add_animator(PROP_OPACITY, 0.0, 1.0, 250)
                return

            case "wclose":
                self._add_animator("pos", pos,
                    QPoint(pos.x() + size.width() // 4, pos.y() + size.height() // 4),
                    250)
                self._add_animator("size",
                    size, QSize(size.width() // 2, size.height() // 2), 250)
                self._add_animator(PROP_OPACITY, 1.0, 0.0, 250)
                return

            case "mopen":
                self._add_animator("pos",
                    QPoint(pos.x() + size.width() // 4, pos.y() + size.height() // 8),
                    pos, 250)
                self._add_animator("size",
                    QSize(size.width() // 2, size.height() // 2), size, 250)
                self._add_animator(PROP_OPACITY, 0.0, 1.0, 250)
                return

            case "mclose":
                self._add_animator("pos", pos,
                    QPoint(pos.x() + size.width() // 4, pos.y() + size.height() // 8),
                    250)
                self._add_animator("size",
                    size, QSize(size.width() // 2, size.height() // 2), 250)
                self._add_animator(PROP_OPACITY, 1.0, 0.0, 250)
                return
            
            case "sbopen":
                self._set_instant("size", size)
                self._add_animator("pos",
                    QPoint(pos.x() + size.width(), 0), pos, 250)
                self._add_animator(PROP_OPACITY, 0.0, 1.0, 250)
                return

            case "sbclose":
                self._set_instant("size", size)
                self._add_animator("pos", pos,
                    QPoint(pos.x() + size.width(), 0), 250)
                self._add_animator(PROP_OPACITY, 1.0, 0.0, 250)
                return

            case "planim":
                self._set_instant("pos", QPoint(0, 0))
                self._add_animator("size",
                    self.pixmap.size(), size, 250)
                return

            case _:
                self._finish_now()
                return

    def _maybe_finish(self):
        if any(a._running for a in self._animators):
            return
        self._finish_now()

    def _finish_now(self):
        if self._on_finished is None:
            return
        cb = self._on_finished
        self._on_finished = None
        for a in self._animators:
            a._running = False
        if callable(cb):
            try:
                cb()
            except Exception:
                pass
        self.close()

    def invoke_update(self):
        any_dirty = False
        for a in list(self._animators):
            if a.invoke_update():
                any_dirty = True
        return any_dirty

    def paintEvent(self, event):
        if self.pixmap.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.drawPixmap(self.rect(), self.pixmap)

    def moveEvent(self, event):
        super().moveEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)