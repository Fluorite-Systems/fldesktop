from PySide6.QtWidgets import QMenu, QPushButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import QPoint


class TrayIcon(QPushButton):
    def __init__(self):
        super().__init__()

        self.setObjectName("traybtn")
        self.setFixedHeight(26)
        self.setIcon(QIcon.fromTheme("system-shutdown-symbolic"))



class PowerOpts:
    def __init__(self, comm):
        
        self.icon = TrayIcon()

        self.menu = QMenu()

        self.logout_act = self.menu.addAction(
            QIcon.fromTheme("system-log-out-symbolic"), "Log out"
        )
        self.logout_act.triggered.connect(
            lambda: comm.send("osmgr", "logout")
        )

        self.lock_act = self.menu.addAction(
            QIcon.fromTheme("lock-symbolic"), "Lock"
        )
        self.lock_act.triggered.connect(
            lambda: comm.send("lockscreen", "show")
        )
        

        self.icon.clicked.connect(
            lambda: self.menu.exec(self.icon.mapToGlobal(
                QPoint(0, self.icon.height())))
        )