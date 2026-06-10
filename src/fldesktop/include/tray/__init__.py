from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QCalendarWidget)
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon

from time import strftime

from fldesktop.include import menu
from fldesktop.include.tray.modules import all_modules
        

class Tray:
    def __init__(self, comm):
        self.comm = comm
        self.icons = []
        self.layout = QHBoxLayout()

        self.load_modules()
    
    def load_modules(self):
        for i in all_modules:
            m = i(self.comm)
            self.layout.addWidget(m.icon)