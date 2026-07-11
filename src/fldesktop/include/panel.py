from PySide6.QtWidgets import (QLabel, QHBoxLayout, QPushButton)
from PySide6.QtCore import Qt, QSize

from fldesktop.include.quickcontrols import (QuickControls, calendar,
                                             kbindicator)
from fldesktop.include.widgets.surface import Surface


class Panel(Surface):
    def __init__(self, parent, comm):
        super().__init__(comm, parent, 5)
        self.desktop = parent
        self.comm = comm
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop)

        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        self.comm.register("panel", {
            "raise": self.raise_,
            "add_minimized": self.add_minimized
        })

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.search_btn = self.comm.request("search", "get_btn")
        self.layout.addWidget(self.search_btn)

        self.minimized_layout = QHBoxLayout()
        self.minimized_layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addLayout(self.minimized_layout)

        self.layout.addStretch()

        self.ki = kbindicator.KeyboardIndicator(self.comm)
        self.layout.addWidget(self.ki.btn)

        self.cal = calendar.Calendar(self.comm)
        self.layout.addWidget(self.cal.btn)

        self.qc = QuickControls(self.comm)
        self.layout.addWidget(self.qc.btn)

        self.setObjectName("panel")
    
    def refresh_geometry(self):
        "Refreshes geometry"
        dsize = self.desktop.size()

        self.setGeometry(0, 0, dsize.width(), 26)

    def add_minimized(self, icon, restore):

        def restore_handler(restore, btn):
            btn.close()
            restore()

        btn = QPushButton(icon=icon)
        #btn.setFixedSize(24, 24)
        btn.setIconSize(QSize(24, 24))
        btn.clicked.connect(
            lambda _, r=restore, b=btn: restore_handler(r, b)
        )

        self.minimized_layout.addWidget(btn)
