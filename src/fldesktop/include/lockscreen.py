from PySide6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton,
                               QVBoxLayout, QHBoxLayout)
from PySide6.QtGui import (QIcon, QPixmap, QFont,
                           QShortcut, QKeySequence)
from PySide6.QtCore import (Qt, QTimer, QTime, QDate, QLocale)
from fldesktop.include.widgets.surface import Surface
import os

import pam


class LockScreen(Surface):
    def __init__(self, parent: QWidget, comm):
        super().__init__(comm, parent, 5)

        self.parent = parent

        self.comm = comm
        self.comm.register("lockscreen", {
            "show": self.show_,
            "refresh_size": self.refresh_size,
        })

        self.mlayout = QHBoxLayout(self)
        self.layout = QVBoxLayout()

        self.mlayout.addStretch()
        self.mlayout.addLayout(self.layout)
        self.mlayout.addStretch()

        self.pwlayout = QHBoxLayout()

        self.pwedit = QLineEdit()
        self.pwedit.setEchoMode(self.pwedit.echoMode().Password)
        self.pwedit.setFixedWidth(200)
        self.ulbtn = QPushButton()
        self.ulbtn.setIcon(QIcon.fromTheme("unlock-symbolic"))
        self.ulbtn.clicked.connect(self.unlock)

        self.ulsc = QShortcut(QKeySequence("Return"), self.pwedit)
        self.ulsc.activated.connect(self.unlock)

        self.pwlayout.addStretch()
        self.pwlayout.addWidget(self.pwedit)
        self.pwlayout.addWidget(self.ulbtn)
        self.pwlayout.addStretch()

        self.clock = QLabel()
        self.clock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clock.setFont(QFont("Noto Sans", 48))

        self.date = QLabel()
        self.date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date.setFont(QFont("Noto Sans", 16))

        self.message = QLabel()
        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message.setFont(QFont("Noto Sans", 14, italic=True))

        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.clock_tick)
        self.clock_timer.start(1000)

        self.layout.addStretch()
        self.layout.addWidget(self.clock)
        self.layout.addWidget(self.date)
        self.layout.addStretch()
        self.layout.addLayout(self.pwlayout)
        self.layout.addWidget(self.message)
        self.layout.addStretch()
        
        self.pwedit.textChanged.connect(lambda: self.message.setText(""))

        self.hide()

        self.clock_tick()
    
    def clock_tick(self):
        "Refresh clock"

        time = QTime.currentTime()
        date = QDate.currentDate()
        hrtime = time.toString("hh:mm")
        hrdate = "думаете я знаю как дату вывести????"

        self.clock.setText(hrtime)
        self.date.setText(hrdate)
    
    def show_(self):
        "Show"

        self.raise_()
        self.show()
        self.refresh_size()
    
    def unlock(self):
        "Attempt an unlock"

        if pam.authenticate(os.getlogin(), self.pwedit.text()):
            self.hide()
            self.pwedit.setText(None)
        else:
            self.message.setText("Failed to unlock")
    
    def refresh_size(self):
        "Refreshes size"

        self.setFixedSize(self.parent.size())
        self.move(0, 0)