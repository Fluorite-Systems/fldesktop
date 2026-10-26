from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtGui import QColor, QPainter

from fldesktop.include.widgets.surface import Surface
from fldesktop.include.superfx import PROP_OPACITY


import time


class FadeEffect(Surface):
    def __init__(self, comm):
        super().__init__(comm, glass=False, layer=999)

        self.comm = comm
        self.comm.register("fade_effect", {
            "fadein": self.fadein,
            "fadeout": self.fadeout,
        })

        self._fade_alpha = 0
        self._fade_running = False
        self._fade_mode = None
        self._fade_start_t = 0.0
        self._fade_duration = 0.5
        self._fade_on_finished = None

        self.setProperty(PROP_OPACITY, 0.0)
        self.loop = QEventLoop()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 255))

    def _prepare_geometry(self):
        d = self.comm.request("desktop", "get_instance")
        self.setFixedSize(d.size())
        self.move(0, 0)
        self.show()
        self.raise_()

    def _set_alpha(self, a):
        if a < 0:
            a = 0
        elif a > 255:
            a = 255
        self._fade_alpha = a
        self.setProperty(PROP_OPACITY, a / 255.0)
        self.update()

    def _start_fade(self, mode, on_finished=None):
        try:
            self.comm.request("superfx", "force_dematerialize")
        except Exception:
            pass
        self._fade_mode = mode
        self._fade_start_t = time.perf_counter()
        self._fade_running = True
        self._fade_on_finished = on_finished
        if mode == "in":
            self._set_alpha(255)
        else:
            self._set_alpha(0)

    def _finish_fade(self):
        self._fade_running = False
        cb = self._fade_on_finished
        self._fade_on_finished = None
        QTimer.singleShot(50, self._safe_hide)
        if callable(cb):
            try:
                cb()
            except Exception:
                pass

    def _safe_hide(self):
        if self._fade_running:
            return
        self.hide()

    def invoke_update(self):
        if not self._fade_running:
            return False
        now = time.perf_counter()
        t = (now - self._fade_start_t) / self._fade_duration
        done = t >= 1.0
        if done:
            t = 1.0
        if self._fade_mode == "in":
            alpha_f = 1.0 - t
        else:
            alpha_f = t * t * t
        self._set_alpha(int(round(alpha_f * 255)))
        if done:
            self._finish_fade()
        return True

    def fadein(self):
        self._start_fade("in")
        self._prepare_geometry()

    def fadeout(self):
        self._start_fade("out", self.loop.exit)
        self._prepare_geometry()
        self.loop.exec(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)