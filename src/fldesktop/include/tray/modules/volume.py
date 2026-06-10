from PySide6.QtWidgets import (QPushButton, QWidget, QVBoxLayout,
                               QHBoxLayout, QSlider, QLabel,
                               QComboBox)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

from fldesktop.include.menu import Menu

import subprocess
import re


class TrayIcon(QPushButton):
    def __init__(self):
        super().__init__()

        self.setObjectName("traybtn")
        self.setFixedHeight(26)


class VolumeWidget(QWidget):
    def __init__(self, comm, parent):
        super().__init__()

        self.comm = comm
        self.icon = parent.icon
        self.parent = parent

        self.setFixedSize(300, 100)

        self.layout = QVBoxLayout(self)

        self.dslayout = QHBoxLayout()
        self.layout.addLayout(self.dslayout)

        self.dslayout.addWidget(QLabel("Current device:"))
        
        self.dscombobox = QComboBox()
        self.dslayout.addWidget(self.dscombobox)

        self.vollayout = QHBoxLayout()
        self.layout.addLayout(self.vollayout)

        self.mute_btn = QPushButton()
        self.mute_btn.setFlat(True)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMaximum(100)
        self.slider.valueChanged.connect(self.set_volume)

        self.percentage = QLabel("idk%")

        for i in [self.mute_btn, self.slider, self.percentage]:
            self.vollayout.addWidget(i)
        
    def set_volume(self):
        
        vol = self.slider.value()

        if vol >= 66:
            ico = "audio-volume-high-symbolic"
        elif vol < 66 and vol >= 33:
            ico = "audio-volume-medium-symbolic"
        elif vol < 33 and vol >= 1:
            ico = "audio-volume-low-symbolic"
        else:
            ico = "player-volume-muted-symbolic"
        
        self.mute_btn.setIcon(QIcon.fromTheme(ico))
        self.icon.setIcon(QIcon.fromTheme(ico))
        self.percentage.setText(str(vol))

        self.parent.set_volume(vol)


class Volume:
    def __init__(self, comm):
        
        self.icon = TrayIcon()

        self.w = VolumeWidget(comm, self)

        self.menu = Menu(
            comm, self.w, self.icon,
            comm.request("desktop", "get_instance")
        )

        self.icon.clicked.connect(self.menu.open)

        self.sink = 0
        self.controller_name = ""
        self.get_info()
    
    def get_info(self):
        result = subprocess.run(['wpctl', 'status'], capture_output=True, text=True)
        output = result.stdout
        pattern = r'\*+\s+(\d+)\.\s+([^\[]+)\[vol:\s*([\d.]+)\]'
        for line in output.split('\n'):
            match = re.search(pattern, line)
            if match:
                self.sink = match.group(1)
                self.controller_name = match.group(2).strip()
                self.volume = int(float(match.group(3)) * 100)
                self.w.slider.setValue(self.volume)
        return None
    
    def set_volume(self, volume):

        subprocess.run(["wpctl", "set-volume", str(self.sink), str(volume) + "%"])