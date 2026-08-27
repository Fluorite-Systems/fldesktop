from PySide6.QtWidgets import (QToolButton, QWidget, QLabel, QLineEdit, 
                               QPushButton, QVBoxLayout, QHBoxLayout,
                               QSizePolicy)
from PySide6.QtGui import QIcon, QFont, QShortcut, QKeySequence
from PySide6.QtCore import Qt, QTimer, QTime, QDate, QLocale
from fldesktop.include.widgets.surface import Surface


class PasswordUnlockBackend(QWidget):
    def __init__(self, manager):
        super().__init__()

        self.comm = manager.comm
        self.manager = manager

        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        self.layout = QVBoxLayout(self)

        self.inp_layout = QHBoxLayout()
        self.layout.addLayout(self.inp_layout)

        self.pwedit = QLineEdit()
        self.pwedit.setEchoMode(self.pwedit.echoMode().Password)
        self.pwedit.setFixedWidth(200)

        self.ulbtn = QToolButton()
        self.ulbtn.setIcon(QIcon.fromTheme("unlock-symbolic"))
        self.ulbtn.clicked.connect(self.unlock)

        self.inp_layout.addStretch()
        self.inp_layout.addWidget(self.pwedit)
        self.inp_layout.addWidget(self.ulbtn)
        self.inp_layout.addStretch()

    def unlock(self):
        
        if self.comm.request(
            "loginmgr", "check_password", self.pwedit.text()
        ):
            self.manager.unlock()


class PasswordlessUnlockBackend(QWidget):
    def __init__(self, manager):
        super().__init__()

        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.layout = QVBoxLayout(self)

        self.ulbtn = QPushButton(
            manager.comm.request("localemgr", "tr", "Unlock"),
            flat=True
        )
        self.ulbtn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.ulbtn.setIcon(QIcon.fromTheme("unlock-symbolic"))
        self.ulbtn.clicked.connect(manager.unlock)

        self.layout.addWidget(
            self.ulbtn, alignment=Qt.AlignmentFlag.AlignCenter
        )


class UnlockBackendManager:
    def __init__(self, lockscreen):

        self.comm = lockscreen.comm
        self.lockscreen = lockscreen

        self.backends = {
            "passwordless": PasswordlessUnlockBackend,
            "password": PasswordUnlockBackend
        }

        self.backend = None

        self.widget = QWidget()
        self._layout = QVBoxLayout(self.widget)

    def setup(self):
        backend_type = self.comm.request("cfgmgr", "get", "auth-type")

        if self.backend is not None:
            self.backend.close()

        if backend_type in self.backends:
            self.backend = self.backends[backend_type](self)
        else:
            self.backend = PasswordlessUnlockBackend(self)

        self._layout.addWidget(self.backend)

    def unlock(self):
        self.lockscreen.hide_()


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

        self.bkmgr = UnlockBackendManager(self)

        self.mlayout = QHBoxLayout(self)
        self.layout = QVBoxLayout()

        self.mlayout.addStretch()
        self.mlayout.addLayout(self.layout)
        self.mlayout.addStretch() 

        self.clock = QLabel()
        self.clock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clock.setFont(QFont("Noto Sans", 48))

        self.date = QLabel()
        self.date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date.setFont(QFont("Noto Sans", 16))

        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.clock_tick)
        self.clock_timer.start(1000)

        self.layout.addStretch()
        self.layout.addWidget(self.clock)
        self.layout.addWidget(self.date)
        self.layout.addStretch()
        self.layout.addWidget(self.bkmgr.widget)
        self.layout.addStretch()

        self.qc_btn = None
        self.first_show = True

        self.hide()

        self.clock_tick()
    
    def clock_tick(self) -> None:
        "Refresh clock"

        locale = QLocale(
            self.comm.request("cfgmgr", "get", "language")
        )
        df = locale.dateFormat(QLocale.FormatType.LongFormat)

        time = QTime.currentTime()
        date = QDate.currentDate()
        hrtime = time.toString("hh:mm")
        hrdate = locale.toString(date, df)

        self.clock.setText(hrtime)
        self.date.setText(hrdate)
    
    def show_(self) -> None:
        "Show"

        atype = self.comm.request("cfgmgr", "get", "auth-type")
        if atype == "passwordless" and self.first_show:
            self.first_show = False
            return

        self.bkmgr.setup()
        self.qc_btn = self.comm.request("panel", "get_qc_btn")
        self.qc_btn.setParent(self.parent)
        self.qc_btn.show()          
        self.raise_()
        self.show()
        self.refresh_size()
        self.qc_btn.raise_()

    def hide_(self) -> None:
        "Hide lockscreen after unlock"
 
        self.hide()
        self.comm.request("panel", "return_qc_btn")
        self.qc_btn = None
    
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
