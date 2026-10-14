from PySide6.QtWidgets import QLabel
from PySide6.QtCore import QTimer

from fldesktop.include.uikit.applet import Applet
from fldesktop.include.thememgr import STD_COLORS

from time import strftime


class Calendar(Applet):
    def __init__(self, comm):
        super().__init__(comm, "", {})

        self.cal = QLabel("there schould be some kind of calendar...", wordWrap=True)
        self.cal.setMaximumSize(350, 300)
        self.cal.setMinimumSize(100, 100)
        self.qlayout.addWidget(self.cal)
        self.qlayout.setContentsMargins(5, 5, 5, 5)

        self.widget.setMaximumSize(self.cal.width() + 5, self.cal.height() + 5)

        self.menu.sync_size()

        self.timer = QTimer(interval=1000)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()


    def refresh(self):

        text = strftime("%H:%M")

        self.attrs["Attr.UI.Applet.ButtonText"] = text
        self.apply_attrs()