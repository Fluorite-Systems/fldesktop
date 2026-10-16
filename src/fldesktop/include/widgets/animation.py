from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtCore import QPoint, QSize, Qt

from fldesktop.include.widgets.surface import Surface

import time


def _out_quart(t):
    u = 1.0 - t
    return 1.0 - u * u * u * u


def _lerp_point(a, b, t):
    return QPoint(
        int(a.x() + (b.x() - a.x()) * t),
        int(a.y() + (b.y() - a.y()) * t))


def _lerp_size(a, b, t):
    return QSize(
        int(a.width() + (b.width() - a.width()) * t),
        int(a.height() + (b.height() - a.height()) * t))


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

        self._start_pos = QPoint(0, 0)
        self._end_pos = QPoint(0, 0)
        self._start_size = QSize(0, 0)
        self._end_size = QSize(0, 0)

        self._duration_ms = 150
        self._start_t = 0.0
        self._end_t = 0.0
        self._on_finished = on_finished
        self._running = False
        self._size_changes = False
        self._last_pos = QPoint(-1, -1)
        self._last_size = QSize(-1, -1)

        self.show()
        self.raise_()

        if not comm.request("lockscreen", "is_visible"):
            comm.request("panel", "raise")

        if "glow_enabled" in params:
            if not params["glow_enabled"]:
                self.set_glow_enabled(False)

        self.animate(type, params, on_finished)

    def animate(self, type: str, params: dict, on_finished):
        self._on_finished = on_finished

        match type:
            case "wmaximize":
                self._duration_ms = 150
                self._size_changes = True
                self._start_pos = QPoint(
                    params["pos"].x() + 50,
                    params["pos"].y() + 50)
                self._end_pos = params["pos"]
                self._start_size = QSize(
                    params["size"].width() - 100,
                    params["size"].height() - 100)
                self._end_size = params["size"]

            case "wunmaximize":
                self._duration_ms = 150
                self._size_changes = True
                self._start_pos = QPoint(
                    params["pos"].x() - 50,
                    params["pos"].y() - 50)
                self._end_pos = params["pos"]
                self._start_size = QSize(
                    params["size"].width() + 100,
                    params["size"].height() + 100)
                self._end_size = params["size"]

            case "wminimize":
                self._duration_ms = 150
                self._size_changes = True
                self._start_pos = params["pos"]
                self._end_pos = QPoint(
                    params["pos"].x() // 2,
                    params["pos"].y() // 2)
                self._start_size = params["size"]
                self._end_size = QSize(0, 0)

            case "wunminimize":
                self._duration_ms = 150
                self._size_changes = True
                self._start_pos = QPoint(
                    params["pos"].x() - 100,
                    params["pos"].y() - 100)
                self._end_pos = params["pos"]
                self._start_size = QSize(
                    params["size"].width() - 100,
                    params["size"].height() - 100)
                self._end_size = params["size"]

            case "wopen":
                self._duration_ms = 250
                self._size_changes = True
                self._start_pos = QPoint(
                    params["pos"].x(),
                    params["pos"].y() + params["size"].width() // 2)
                self._end_pos = params["pos"]
                self._start_size = QSize(params["size"].width(), 0)
                self._end_size = params["size"]

            case "wclose":
                self._duration_ms = 250
                self._size_changes = True
                self._start_pos = params["pos"]
                self._end_pos = QPoint(
                    params["pos"].x(),
                    params["pos"].y() + params["size"].height() // 2)
                self._start_size = params["size"]
                self._end_size = QSize(params["size"].width(), 0)

            case "mopen":
                self._duration_ms = 150
                self._size_changes = False
                self._start_pos = QPoint(
                    params["pos"].x(),
                    -params["size"].height())
                self._end_pos = params["pos"]
                self._start_size = params["size"]
                self._end_size = params["size"]

            case "mclose":
                self._duration_ms = 150
                self._size_changes = False
                self._start_pos = params["pos"]
                self._end_pos = QPoint(
                    params["pos"].x(),
                    -params["size"].height())
                self._start_size = params["size"]
                self._end_size = params["size"]

            case "sbopen":
                self._duration_ms = 150
                self._size_changes = False
                self._start_pos = QPoint(
                    params["pos"].x() + params["size"].width(), 0)
                self._end_pos = params["pos"]
                self._start_size = params["size"]
                self._end_size = params["size"]

            case "sbclose":
                self._duration_ms = 150
                self._size_changes = False
                self._start_pos = params["pos"]
                self._end_pos = QPoint(
                    params["pos"].x() + params["size"].width(), 0)
                self._start_size = params["size"]
                self._end_size = params["size"]

            case "planim":
                self._duration_ms = 150
                self._size_changes = True
                self._start_pos = QPoint(0, 0)
                self._end_pos = QPoint(0, 0)
                self._start_size = self.pixmap.size()
                self._end_size = params["size"]

            case _:
                self._duration_ms = 0
                self._size_changes = False
                self._start_pos = params["pos"]
                self._end_pos = params["pos"]
                self._start_size = params["size"]
                self._end_size = params["size"]

        self.move(self._start_pos)
        self.resize(self._start_size)

        self._last_pos = self._start_pos
        self._last_size = self._start_size

        self._start_t = time.perf_counter()
        self._end_t = self._start_t + self._duration_ms / 1000.0
        self._running = self._duration_ms > 0

        if not self._running:
            self._finish_now()

    def invoke_update(self):
        if not self._running:
            return False

        now = time.perf_counter()
        if now >= self._end_t:
            self.setGeometry(
                self._end_pos.x(), self._end_pos.y(),
                self._end_size.width(), self._end_size.height())
            self._last_pos = self._end_pos
            self._last_size = self._end_size
            self._running = False
            self._finish_now()
            return True

        t = (now - self._start_t) / (self._end_t - self._start_t)
        eased = _out_quart(t)

        p = _lerp_point(self._start_pos, self._end_pos, eased)
        s = _lerp_size(self._start_size, self._end_size, eased)

        moved = (p != self._last_pos)
        resized = (s != self._last_size)

        if moved or resized:
            self._last_pos = p
            self._last_size = s
            self.setGeometry(p.x(), p.y(), s.width(), s.height())

        if resized and self._size_changes:
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
        self.close()

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