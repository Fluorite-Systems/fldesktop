from PySide6.QtWidgets import QApplication, QWidget, QMenu
from PySide6.QtCore import Qt

from fldesktop.include.widgets.fade_effect import FadeEffect


class Desktop(QWidget):
    def __init__(self, comm) -> None:
        super().__init__()

        self.comm = comm
        self.comm.register("desktop", {
                "get_instance": self.get_instance
            }
        )

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

        #self.bg.setContextMenuPolicy(Qt.CustomContextMenu)
        #self.bg.customContextMenuRequested.connect(
        #    lambda p: self.menu.exec(self.bg.mapToGlobal(p))
        #)

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

        self.comm.request("lockscreen", "refresh_size")
        self.comm.emit("desktop_size_changed")