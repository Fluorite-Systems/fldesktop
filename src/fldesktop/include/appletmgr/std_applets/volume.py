from PySide6.QtWidgets import (QPushButton, QWidget,
                               QHBoxLayout, QSlider, QLabel)
from PySide6.QtCore import Qt, QTimer

from fldesktop.include.uikit.applet import Applet

import subprocess
import re


class VolumeWidget(QWidget):
    def __init__(self, comm):
        super().__init__()

        self.comm = comm

        self.setFixedHeight(50)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.mute_btn = QPushButton()
        self.mute_btn.setFlat(True)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMaximum(100)

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

        if vol > 66:
            ico = "audio-volume-3"
        elif vol > 33:
            ico = "audio-volume-2"
        elif vol > 1:
            ico = "audio-volume-1"
        else:
            ico = "audio-volume-muted"

        icon = self.comm.request("iconmgr", "get", ico)
        
        self.mute_btn.setIcon(icon)
        self.comm.request("qc_indicator", "add_icon", icon, "volume")
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
                break


class Volume(Applet):
    def __init__(self, comm):
        super().__init__(comm, "", {})

        self.vw = VolumeWidget(self.comm)
        self.vw.slider.valueChanged.connect(self.set_volume)
        self.qlayout.addWidget(self.vw)

        self.qlayout.setContentsMargins(5, 5, 5, 5)

        self.widget.setMaximumWidth(200)
        self.widget.setMinimumWidth(100)
        self.widget.setMaximumHeight(50)
        self.menu.sync_size()

        self.set_volume()

    def set_volume(self):
        self.vw.set_volume()

        self.attrs["Attr.UI.Applet.QIcon"] = self.vw.mute_btn.icon()
        self.apply_attrs()