from math import sin

from PySide6.QtWidgets import (QPushButton, QWidget,
                               QHBoxLayout, QSlider, QLabel)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QTimer

import subprocess
import re


class Volume(QWidget):
    def __init__(self, comm, parent):
        super().__init__()

        self.comm = comm

        self.setFixedHeight(50)

        self.layout = QHBoxLayout(self)
        self.mute_btn = QPushButton()
        self.mute_btn.setFlat(True)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMaximum(100)
        self.slider.valueChanged.connect(self.set_volume)

        self.percentage = QLabel("idk%")

        for i in [self.mute_btn, self.slider, self.percentage]:
            self.layout.addWidget(i)

        self.timer = QTimer(interval=300, singleShot=True)
        self.timer.timeout.connect(self.apply_volume)

        self.sink = 0
        self.controller_name = ""
        self.get_info()
        
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
        self.comm.send("qc_indicator", "add_icon", 
                       QIcon.fromTheme(ico), "volume")
        self.percentage.setText(str(vol))

        self.timer.start()
    
    def apply_volume(self):

        vol = self.slider.value()
        subprocess.run(["wpctl", "set-volume", str(self.sink), str(vol) + "%"])

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
                self.slider.setValue(self.volume)
                self.set_volume()