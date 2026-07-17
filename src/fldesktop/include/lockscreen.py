from PySide6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton,
                               QVBoxLayout, QHBoxLayout, QMenu)
from PySide6.QtGui import (QIcon, QPixmap, QFont,
                           QShortcut, QKeySequence)
from PySide6.QtCore import (Qt, QTimer, QTime, QDate, QLocale, QPoint)
from fldesktop.include.widgets.surface import Surface


class LockScreen(Surface):
    def __init__(self, comm) -> None:

        parent = comm.request("desktop", "get_instance")
        
        super().__init__(comm, parent, 5)

        self.parent = parent

        self.comm = comm
        self.comm.register("lockscreen", {
            "show": self.show_,
            "refresh_size": self.refresh_size,
            "is_visible": self.is_visible,
            "raise": self.raise_,
            "raise_qc_btn": self.raise_qc_btn
        })

        self.comm.subscribe("qc_btn_size_changed", self.refresh_size)

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

        self.powerbtn = QPushButton(
            self,
            icon=QIcon.fromTheme("system-shutdown-symbolic"),
            flat=True
        )
        self.powerbtn.setFixedSize(32, 32)
        self.powerbtn.show()

        self.powermenu = QMenu()

        self.powerbtn.clicked.connect(
            lambda: self.powermenu.exec(
                self.powerbtn.mapToGlobal(
                   self.powerbtn.pos()
                )
            )
        )

        actions = [
            (self.comm.request("localemgr", "tr", "Sleep"),
                "system-suspend-symbolic", lambda: ...),
            (self.comm.request("localemgr", "tr", "Shutdown"),
                "system-shutdown-symbolic", lambda: ...),
            (self.comm.request("localemgr", "tr", "Reboot"),
                "system-reboot-symbolic", lambda: ...)
        ]

        for i in actions:
            a = self.powermenu.addAction(QIcon.fromTheme(i[1]), i[0])
            a.triggered.connect(i[2])

        self.qc_btn = None

        self.hide()

        self.clock_tick()
    
    def clock_tick(self) -> None:
        "Refresh clock"

        time = QTime.currentTime()
        date = QDate.currentDate()
        hrtime = time.toString("hh:mm")
        hrdate = "думаете я знаю как дату вывести????"

        self.clock.setText(hrtime)
        self.date.setText(hrdate)
    
    def show_(self) -> None:
        "Show"

        if self.comm.request("loginmgr", "is_available"):
            self.qc_btn = self.comm.request("panel", "get_qc_btn")
            self.qc_btn.setParent(self.parent)
            self.qc_btn.show()          
            self.raise_()
            self.show()
            self.refresh_size()
            self.qc_btn.raise_()
        else:
            ...
    
    def unlock(self) -> None:
        "Attempt an unlock"

        if self.comm.request("loginmgr", "check_password", self.pwedit.text()): #pam.authenticate(os.getlogin(), self.pwedit.text()):
            self.hide()
            self.comm.send("panel", "return_qc_btn")
            self.qc_btn = None
            self.pwedit.setText(None)
        else:
            self.message.setText("Failed to unlock")
    
    def refresh_size(self) -> None:
        "Refreshes size"

        self.setFixedSize(self.parent.size())
        self.move(0, 0)

        if self.qc_btn:
            self.qc_btn.move(self.width() - self.qc_btn.width(), 0)

    def is_visible(self) -> bool:

        return self.isVisible()

    def raise_qc_btn(self) -> None:

        if self.qc_btn:
            self.qc_btn.raise_()

    def resizeEvent(self, event) -> None:
        self.powerbtn.move(
            self.width() - self.powerbtn.width(),
            self.height() - self.powerbtn.height()
        )
        super().resizeEvent(event)
