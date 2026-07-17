from PySide6.QtWidgets import (QWidget, QPushButton, QLabel,
                               QHBoxLayout, QVBoxLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from fldesktop.include.menu import Menu
from fldesktop.include.quickcontrols.modules import all_modules


class Button(QPushButton):
    def __init__(self, comm):
        super().__init__()
        self.comm = comm
        self.comm.register("qc_indicator", {
            "add_icon": self.add_icon,
            "remove_icon": self.remove_icon
        }
        )

        self.setFlat(True)
        self.setObjectName("traybtn")

        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(2)
        self.layout.setDirection(QHBoxLayout.Direction.RightToLeft)
        self.icons = {}

        self.add_icon(
            self.comm.request("iconmgr", "get", "shutdown"), "shutdown"
        )
    
    def add_icon(self, icon: QIcon, id: str):
        
        pm = icon.pixmap(16, 16)

        if not id in self.icons:
            iw = QLabel(pixmap=pm)
            self.icons[id] = iw
            self.layout.addWidget(iw)
        else:
            self.icons[id].setPixmap(pm)

        self.refresh_size()

        self.comm.emit("qc_btn_size_changed")
    
    def remove_icon(self):
        ...
    
    def refresh_size(self):

        nw = self.layout.count() * 16
        nw += self.layout.spacing() * (self.layout.count() - 1)
        nw += self.layout.contentsMargins().right() +\
            self.layout.contentsMargins().left()
        self.setFixedWidth(nw)
        

class QuickControls(QWidget):
    def __init__(self, comm):
        super().__init__()
        self.comm = comm

        self.layout = QVBoxLayout(self)

        self.btn = Button(comm)

        self.load_modules()

        self.menu = Menu(
            self.comm, self, self.btn,
            self.comm.request("desktop", "get_instance")
        )
        self.btn.clicked.connect(self.menu.open)

    
    def load_modules(self):
        nsize = 10
        for i in all_modules:
            m = i(self.comm, self)
            self.layout.addWidget(m)
            nsize += m.height()

        self.layout.addStretch()
        self.setFixedSize(300, nsize)
