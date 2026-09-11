from PySide6.QtWidgets import QHBoxLayout, QPushButton, QSizePolicy
from PySide6.QtCore import Qt, QSize

from fldesktop.include.quickcontrols import (QuickControls, calendar,
                                             kbindicator)
from fldesktop.include.widgets.surface import Surface


class AppBtn(QPushButton):
    def __init__(self, id: int, title: str, icon):
        super().__init__()

        self.id = id

        self.setIconSize(QSize(24, 24))
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setObjectName("traybtn")
        self.setIcon(icon)
        self.setText(title)

    def set_highlight(self, enabled: bool):

        if enabled:
            self.setStyleSheet("background-color: rgba(200, 200, 200, 100)")
        else:
            self.setStyleSheet("background-color: transparent")

    def set_title(self, title: str):

        self.setText(title)


class Panel(Surface):
    def __init__(self, parent, comm):
        super().__init__(comm, parent, 5)
        self.desktop = parent
        self.comm = comm
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop)

        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        self.comm.register("panel", {
            "raise": self.raise_,
            "add_btn": self.add_btn,
            "rm_btn": self.rm_btn,
            "highlight_btn": self.highlight_btn,
            "set_btn_text": self.set_btn_text,
            "get_qc_btn": self.get_qc_btn,
            "return_qc_btn": self.return_qc_btn
        })

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.search_btn = self.comm.request("search", "get_btn")
        self.layout.addWidget(self.search_btn)

        self.taskbar_layout = QHBoxLayout()
        self.taskbar_layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addLayout(self.taskbar_layout)

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

    def add_btn(self, id, icon, text, on_click):

        btn = AppBtn(id, text, icon)

        btn.clicked.connect(on_click)

        self.taskbar_layout.addWidget(btn)

    def rm_btn(self, id):

        for i in range(self.taskbar_layout.count()):
            w = self.taskbar_layout.itemAt(i).widget()
            if w.id == id:
                w.close()
                w.deleteLater()

    def highlight_btn(self, id: int, highlighted: bool):

        for i in range(self.taskbar_layout.count()):
            w = self.taskbar_layout.itemAt(i).widget()
            if w.id == id:
                w.set_highlight(highlighted)

    def set_btn_text(self, id: int, text: str):

        for i in range(self.taskbar_layout.count()):
            w = self.taskbar_layout.itemAt(i).widget()
            if w.id == id:
                w.set_title(text)

    def get_qc_btn(self) -> QPushButton:

        self.layout.removeWidget(self.qc.btn)
        return self.qc.btn

    def return_qc_btn(self) -> None:

        self.qc.btn.setParent(None)
        self.layout.addWidget(self.qc.btn)
