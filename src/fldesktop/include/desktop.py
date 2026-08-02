from PySide6.QtWidgets import (QApplication, QMainWindow, QMenu,
                               QLabel)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap, QPainter

from fldesktop.include import panel
from fldesktop.include.widgets.fade_effect import FadeEffect


class Background(QLabel):
    def __init__(self, desktop: Desktop, comm) -> None:
        super().__init__(desktop)

        self.comm = comm

        self.comm.subscribe("reload_config", self.reload)

        self.reload()

    def reload(self):

        btype = self.comm.request("cfgmgr", "get", "background-type")
        color = self.comm.request("cfgmgr", "get", "background-color")
        wp = self.comm.request("cfgmgr", "get", "wallpaper")

        if wp and btype == "wallpaper":
            self.pic = QPixmap(wp)
        else:
            self.pic = QPixmap(10, 10)
            self.pic.fill(QColor(color))

    def refresh(self) -> None:
        "Resizes background"

        parent = self.parent()

        self.setGeometry(0, 0, parent.size().width(), parent.size().height())

        self.setPixmap(self.pic.scaled(parent.size(), 
                            Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                            Qt.TransformationMode.SmoothTransformation)
        )
        self.lower()

        self.comm.request("surfacemgr", "refresh")



class Desktop(QMainWindow):
    def __init__(self, comm) -> None:
        super().__init__()

        self.comm = comm
        self.comm.register("desktop", {
                "get_instance": self.get_instance
            }
        )

        self.panel = panel.Panel(self, self.comm)
        
        self.bg = Background(self, self.comm)

        # Context menu when right-clicked at the background
        self.menu = QMenu()
        self.ch_bg_action = self.menu.addAction(
            self.comm.request("localemgr", "tr", "Change background")
        )
        self.st_action = self.menu.addAction(
            self.comm.request("localemgr", "tr", "Settings")
        )
        self.ch_bg_action.triggered.connect(
            lambda: self.comm.request("pkgmgr", "run_app", "com.example.texted")
        )
        self.st_action.triggered.connect(
            lambda: self.comm.request("pkgmgr", "run_app", "com.example.texted")
        )

        self.bg.setContextMenuPolicy(Qt.CustomContextMenu)
        self.bg.customContextMenuRequested.connect(
            lambda p: self.menu.exec(self.bg.mapToGlobal(p))
        )

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(QApplication.primaryScreen().availableSize())
        self.setWindowTitle("fldesktop")

        self.setMinimumSize(800, 600)

        # Fade effect on startup and shutdown
        self.fade_effect = FadeEffect(self.comm, self)

        self.show()
    
    def get_instance(self):
        "Get desktop instance from comm"

        return self
    
    def resizeEvent(self, event) -> None:

        super().resizeEvent(event)

        self.panel.refresh_geometry()
        self.comm.request("lockscreen", "refresh_size")
        self.bg.refresh()
