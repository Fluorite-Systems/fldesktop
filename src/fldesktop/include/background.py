import os
from PySide6.QtCore import Qt, QUrl, QRectF, QTimer
from PySide6.QtGui import QPainter, QPixmap, QColor
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtMultimedia import QMediaPlayer, QVideoSink

from fldesktop.include.widgets.surface import Surface


class VideoCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAutoFillBackground(False)

        self.video_sink = QVideoSink(self)
        self._image = None
        self._has_frame = False

        self._compositor_notify = None

        self._pump = QTimer(self)
        self._pump.setTimerType(Qt.TimerType.PreciseTimer)
        self._pump.setInterval(16)
        self._pump.timeout.connect(self._on_pump)

        self.video_sink.videoFrameChanged.connect(self._on_frame_changed)

    def set_compositor_notify(self, cb):
        self._compositor_notify = cb

    def start_pump(self):
        if not self._pump.isActive():
            self._pump.start()

    def stop_pump(self):
        self._pump.stop()

    def _on_frame_changed(self, frame):
        if not frame.isValid():
            return
        try:
            img = frame.toImage()
        except Exception:
            return
        if img.isNull():
            return
        self._image = img
        self._has_frame = True
        self.update()
        self._notify()

    def _on_pump(self):
        if self._has_frame:
            self._notify()

    def _notify(self):
        cb = self._compositor_notify
        if cb is None:
            return
        try:
            cb()
        except Exception:
            pass

    def paintEvent(self, event):
        painter = QPainter(self)
        img = self._image
        if img is None or img.isNull():
            painter.fillRect(self.rect(), Qt.GlobalColor.black)
            return
        w = self.width()
        h = self.height()
        if w <= 0 or h <= 0:
            return
        scaled = img.scaled(
            w, h,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation)
        sx = max(0, (scaled.width() - w) // 2)
        sy = max(0, (scaled.height() - h) // 2)
        painter.drawImage(
            QRectF(0, 0, w, h),
            scaled,
            QRectF(sx, sy, w, h))

    def release_frame(self):
        self._image = None
        self._has_frame = False
        self.stop_pump()


class VideoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.view = VideoCanvas(self)
        self.layout.addWidget(self.view)


class Background(Surface):
    def __init__(self, comm) -> None:
        super().__init__(
            comm, layer=0, layer_lock=True, glass=False,
            never_materialize=True
        )

        self.comm = comm

        self.pic_view = QLabel(self)
        self.pic = QPixmap(10, 10)
        self.pic.fill(Qt.GlobalColor.darkGray)

        self.video_player = QMediaPlayer(
            loops=QMediaPlayer.Loops.Infinite)
        self.video_view = VideoWidget(self)
        self.video_player.setVideoSink(self.video_view.view.video_sink)

        self.video_view.view.set_compositor_notify(
            self._notify_compositor)

        self.comm.subscribe("reload_config", self.reload)
        self.comm.subscribe("desktop_size_changed", self.refresh)

        self.load_bg()

        self.lower()
        self.show()
        self.refresh()

    def _notify_compositor(self):
        try:
            self.comm.request("superfx", "invalidate", self)
        except Exception:
            pass

    def show_video(self):
        self.video_view.show()
        self.pic_view.hide()
        try:
            self.video_view.view.start_pump()
        except Exception:
            pass

    def show_pic(self):
        self.pic_view.show()
        self.video_view.hide()
        try:
            self.video_view.view.stop_pump()
        except Exception:
            pass

    def load_bg(self) -> None:
        btype = self.comm.request("cfgmgr", "get", "background-type")
        color = self.comm.request("cfgmgr", "get", "background-color")
        wp = self.comm.request("cfgmgr", "get", "wallpaper")

        if os.path.exists(wp) and btype == "wallpaper":
            self.show_pic()
            self.pic = QPixmap(wp)
        elif os.path.exists(wp) and btype == "video":
            self.show_video()
            self.video_player.setSource(QUrl.fromLocalFile(wp))
            self.video_player.play()
        else:
            self.show_pic()
            self.pic = QPixmap(10, 10)
            self.pic.fill(QColor(color))

    def reload(self) -> None:
        self.load_bg()
        self.refresh()

    def refresh(self) -> None:
        parent = self.comm.request("desktop", "get_instance")

        self.setFixedSize(parent.size())
        self.pic_view.setFixedSize(self.size())
        self.video_view.setFixedSize(self.size())

        self.pic_view.setPixmap(
            self.pic.scaled(
                parent.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.lower()

        self.comm.request("surfacemgr", "refresh")

    def cleanup(self):
        try:
            if (hasattr(self, 'video_view')
                    and self.video_view is not None
                    and hasattr(self.video_view, 'view')
                    and self.video_view.view is not None):
                self.video_view.view.stop_pump()
                self.video_view.view.set_compositor_notify(None)
                self.video_view.view.release_frame()
        except (RuntimeError, SystemError):
            pass

        try:
            if getattr(self, 'video_player', None) is not None:
                self.video_player.stop()
                self.video_player.setVideoSink(None)
                self.video_player.setSource(QUrl())
        except (RuntimeError, SystemError):
            pass
        finally:
            self.video_player = None

    def closeEvent(self, event):
        self.cleanup()
        super().closeEvent(event)