from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QPainter, QColor, QBrush, QRadialGradient, QPixmap
from PySide6.QtCore import Qt, QTimer, QPointF

import subprocess
import math
import os
import platform


class ProgressBar(QWidget):
    def __init__(self, color: QColor):
        super().__init__()

        self.setFixedHeight(50)

        self._x = 0
        self._color = color
        self._adv_timer = QTimer(self, interval=10)
        self._adv_timer.timeout.connect(self._adv)

    def _adv(self):

        if self._x < self.width():
            self._x += 1
        else:
            self._x = 0

        self.update()

    def paintEvent(self, event):
        if self.width() <= 0 or self.height() <= 0: return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center_x = self._x
        center_y = self.height() / 2
        progress = center_x / self.width()
        
        sin_value = math.sin(progress * math.pi)
        
        radius = max(1.0, (self.height() * 0.85) * sin_value)

        gradient = QRadialGradient(QPointF(center_x, center_y), radius)

        for i in range(16):
            pos = i / 15.0
            color = QColor(self._color)

            alpha_factor = (1.0 - pos) ** 4.0
            color.setAlphaF(sin_value * alpha_factor)
            
            gradient.setColorAt(pos, color)

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)

        painter.drawRect(self.rect())

    def showEvent(self, event):
        self._adv_timer.start()
        return super().showEvent(event)

    def hideEvent(self, event):
        self._adv_timer.stop()
        return super().hideEvent(event)


class StartupScreen(QWidget):
    def __init__(self, comm):
        super().__init__(comm.request("desktop", "get_instance"))

        self.comm = comm
        self.comm.subscribe("desktop_size_changed", self.refresh_geometry)

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: black;")

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.l = QLabel(pixmap=self.load_dist_logo())
        self.l.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.pb = ProgressBar(self.comm.request(
            "surfacemgr", "get_brightest_spot"
        ).color)
        self.pb.setFixedWidth(250)

        self.layout.addWidget(self.l)
        self.layout.addWidget(self.pb)

    def load_dist_logo(self):

        logo = platform.freedesktop_os_release().get(
            "LOGO", platform.freedesktop_os_release().get("ID", "")
        )

        for ext in (".svg", ".png"):
            path = f"/usr/share/pixmaps/{logo}{ext}"
            if os.path.exists(path):
                return QPixmap(path).scaledToWidth(
                    128, Qt.TransformationMode.SmoothTransformation
                )
                
        return QPixmap()


    def refresh_geometry(self):
        self.resize(self.parent().size())


class ShutdownScreen(QWidget):
    def __init__(self, comm):
        super().__init__(comm.request("desktop", "get_instance"))

        self.comm = comm
        self.comm.subscribe("desktop_size_changed", self.refresh_geometry)

        self.layout = QVBoxLayout(self)
        self.l = QLabel("stopping application")
        self.layout.addWidget(self.l)

    def refresh_geometry(self):
        self.setFixedSize(self.parent().size())


class StartupScreenManager:
    def __init__(self, comm):

        self.comm = comm
        self.comm.register(
            "ssmgr", {
                "show_startup": self.show_startup,
                "show_shutdown": self.show_shutdown
            }
        )

        self.startup = StartupScreen(self.comm)
        self.shutdown = ShutdownScreen(self.comm)

        self.show_startup()

    def show_startup(self):
        self.startup.show()
        self.startup.raise_()
        self.startup.refresh_geometry()

        self.timer = QTimer(singleShot=True, interval=15000)
        self.timer.timeout.connect(self.continue_boot)
        self.timer.start()

    def continue_boot(self):
        self.startup.hide()
        self.comm.request("init", "run", runlevel=3)

    def show_shutdown(self):
        self.shutdown.show()
        self.shutdown.raise_()
        self.shutdown.refresh_geometry()