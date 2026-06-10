from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout)


class Notification(QWidget):
    def __init__(self):
        super().__init__()


class NotificationManager:
    def __init__(self, comm):
        self.comm = comm
        self.comm.register("notifymgr",{
            "notify": self.notify
        })
    
    def notify(self):
        ...