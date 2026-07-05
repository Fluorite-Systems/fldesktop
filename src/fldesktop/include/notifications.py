from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer

from fldesktop.include.widgets.surface import Surface


class Notification(Surface):
    def __init__(self, comm, title: str, body: str,
                 icon: QIcon, parent: QWidget) -> None:
        super().__init__(comm, parent)

        self.comm = comm

        self.setFixedSize(300, 150)
        self.move(
            self.parent().width() - self.width() - 4,
            4 if self.comm.request("lockscreen", "is_visible") else 30
        )

        self.layout = QVBoxLayout(self)
        self.title_layout = QHBoxLayout()
        self.body_layout = QHBoxLayout()

        self.close_btn = QPushButton(
            icon=QIcon.fromTheme("dialog-close-symbolic"),
            flat=True
        )
        self.close_btn.clicked.connect(self.close_)
        self.title_lbl = QLabel(str(title))
        self.body_lbl = QLabel(str(body))
        self.icon = QLabel(pixmap=icon.pixmap(64, 64))

        self.title_layout.addWidget(self.title_lbl)
        self.title_layout.addStretch()
        self.title_layout.addWidget(self.close_btn)

        self.body_layout.addWidget(self.icon)
        self.body_layout.addWidget(self.body_lbl)

        self.layout.addLayout(self.title_layout)
        self.layout.addLayout(self.body_layout)

        self.comm.subscribe("notification_spawned", self.close_)

        QTimer().singleShot(5000, self.close_)

        self.show()
        self.raise_()

    def close_(self) -> None:
        self.comm.unsubscribe(self.close_)
        self.close()
        self.deleteLater()


class NotificationManager:
    def __init__(self, comm) -> None:
        self.comm = comm
        self.comm.register("notifymgr",{
            "notify": self.notify
        })
    
    def notify(self, title, body, icon: QIcon = None) -> None:
        
        if not icon:
            icon = QIcon.fromTheme("dialog-information")

        self.comm.emit("notification_spawned")

        dsk = self.comm.request("desktop", "get_instance")

        n = Notification(self.comm, title, body, icon, dsk)
