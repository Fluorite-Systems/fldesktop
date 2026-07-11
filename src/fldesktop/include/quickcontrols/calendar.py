from PySide6.QtWidgets import (QPushButton, QVBoxLayout,
                               QWidget, QCalendarWidget,
                               QSizePolicy)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer

from fldesktop.include.menu import Menu

from time import strftime


class CalendarWidget(QWidget):
    def __init__(self, comm, icon):
        super().__init__()

        self.comm = comm
        self.icon = icon

        self.setFixedSize(400, 300)

        self.layout = QVBoxLayout(self)

        self.cal = QCalendarWidget()
        self.layout.addWidget(self.cal)


class Calendar:
    def __init__(self, comm):
        
        self.btn = QPushButton()
        self.btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn.setObjectName("traybtn")

        self.w = CalendarWidget(comm, self.btn)

        self.menu = Menu(
            comm, self.w, self.btn,
            comm.request("desktop", "get_instance")
        )

        self.btn.clicked.connect(self.menu.open)

        self.timer = QTimer(interval = 1000)
        self.timer.timeout.connect(self.refresh_clock)
        self.timer.start()

        self.refresh_clock()
    
    def refresh_clock(self):
        "Refreshes the clock"

        text = strftime("%H:%M")

        self.btn.setText(text)
