from PySide6.QtWidgets import (QApplication, QMainWindow, QMenu,
                               QLabel)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from fldesktop.include import panel
from fldesktop.include.widgets.fade_effect import FadeEffect


class Desktop(QMainWindow):
    def __init__(self, comm) -> None:
        super().__init__()

        self.comm = comm
        self.comm.register("desktop", {
                "reload": self.reload,
                "get_instance": self.get_instance
            }
        )
        self.comm.subscribe("reload_config", self.reload)

        self.panel = panel.Panel(self, self.comm)
        
        self.bg = QLabel(self)
        self.bgp = QPixmap(self.comm.request("cfgmgr", "get", "background"))

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
    
    def reload(self) -> None:
        "Reloads desktop (primarily bg)"

        self.comm.request("cfgmgr", "reload")
        self.bgp = QPixmap(self.comm.request("cfgmgr", "get", "background"))
        self.refresh_bg()
    
    def get_instance(self):
        "Get desktop instance from comm"

        return self
    
    def refresh_bg(self) -> None:
        "Resizes background"

        self.bg.setGeometry(0, 0, self.size().width(), self.size().height())

        self.bg.setPixmap(self.bgp.scaled(self.size(), 
                            Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                            Qt.TransformationMode.SmoothTransformation)
        )
        self.bg.lower()

        self.comm.request("surfacemgr", "refresh")
    
    def resizeEvent(self, event) -> None:

        super().resizeEvent(event)

        self.panel.refresh_geometry()
        self.comm.request("lockscreen", "refresh_size")
        self.refresh_bg()
