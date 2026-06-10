from PySide6.QtWidgets import (QWidget, QPushButton, QHBoxLayout, QMenu)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QPoint


class Actions(QWidget):
    def __init__(self, comm, parent):
        super().__init__()
        self.comm = comm
        self.parent_ = parent

        self.setFixedHeight(50)

        self.layout = QHBoxLayout(self)

        self.layout.addStretch()

        self.lock_btn = QPushButton()
        self.lock_btn.setFlat(True)
        self.lock_btn.setIcon(QIcon.fromTheme("lock-symbolic"))
        self.lock_btn.clicked.connect(
            lambda: self.action_handler(
                lambda: self.comm.send("lockscreen", "show")
            )
        )

        self.sleep_btn = QPushButton()
        self.sleep_btn.setFlat(True)
        self.sleep_btn.setIcon(QIcon.fromTheme("system-suspend-symbolic"))
        self.sleep_btn.clicked.connect(
            lambda: self.action_handler(
                lambda: self.comm.send("osmgr", "suspend")
            )
        )

        self.pwr_btn = QPushButton()
        self.pwr_btn.setFlat(True)
        self.pwr_btn.setIcon(QIcon.fromTheme("system-shutdown-symbolic"))

        self.pwr_menu = QMenu()
        self.shutdown_act = self.pwr_menu.addAction(
            QIcon.fromTheme("system-shutdown-symbolic"), "Shutdown"
        )
        self.reboot_act = self.pwr_menu.addAction(
            QIcon.fromTheme("system-reboot-symbolic"), "Reboot"
        )
        self.logout_act = self.pwr_menu.addAction(
            QIcon.fromTheme("system-log-out-symbolic"), "Log out"
        )

        self.shutdown_act.triggered.connect(
            lambda: self.action_handler(
                lambda: self.comm.send("osmgr", "poweroff")
            )
        )
        self.reboot_act.triggered.connect(
            lambda: self.action_handler(
                lambda: self.comm.send("osmgr", "reboot")
            )
        )
        self.logout_act.triggered.connect(
            lambda: self.action_handler(
                lambda: self.comm.send("osmgr", "logout")
            )
        )

        self.pwr_btn.clicked.connect(
            lambda: self.pwr_menu.exec(self.pwr_btn.mapToGlobal(
                QPoint(self.pwr_btn.x(), 
                       self.pwr_btn.y() + self.pwr_btn.height())
            ))
        )

        for i in [self.lock_btn, self.sleep_btn, self.pwr_btn]:
            self.layout.addWidget(i)
    
    def action_handler(self, callable):
        self.parent_.menu.close_menu()
        callable()