from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QLabel
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer

from pathlib import Path

import logging


BAT_PATH = Path("/sys/class/power_supply/")


class Battery(QWidget):
    def __init__(self, comm, parent):
        super().__init__()

        self.comm = comm

        self.layout = QVBoxLayout(self)
        self.view = QLabel("")
        self.view.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self.layout.addWidget(self.view)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setFixedHeight(0)

        self.timer = QTimer(interval=3000)
        self.timer.timeout.connect(self.refresh)

        if self.is_battery_present():
            logging.info("Battery present!")
            self.refresh()
            self.timer.start()

    def refresh(self):
        "Refresh"
        
        bats = self.update_bats()

        total_percent, charging = self.sys_bat_percent(bats)

        panel_icon = self.get_icon_by_percent(total_percent, charging)

        self.comm.request("qc_indicator", "add_icon", 
                       QIcon.fromTheme(panel_icon), "battery")

        """text = ""

        for bat in bats:
            if bat["scope"] == "Device":
                text += f"{bat["model_name"]}: {bat["percentage"]}%\n"
        
        if text:
            self.view.setText(text)
            self.setFixedHeight(self.view.sizeHint().height())
        else:
            self.setFixedHeight(0)""" # <== looks awful

    def get_icon_by_percent(self, percent: int, charging: bool) -> str:
        "Get icon name by battery percentage"

        c = "-charging" if charging else ""

        if percent >= 80:
            icon = f"battery-full{c}-symbolic"
        elif percent >= 50:
            icon = f"battery-good{c}-symbolic"
        elif percent >= 20:
            icon = f"battery-low{c}-symbolic"
        elif percent >= 5:
            icon = f"battery-caution{c}-symbolic"
        else:
            icon = f"battery-empty{c}-symbolic"

        return icon

    def sys_bat_percent(self, bats: list) -> tuple[int, bool]:
        "Get total percentage and charging status of every system battery"
        
        total_now = 0
        total_full = 0
        charging = False

        for bat in bats:

            if bat["scope"] != "System":
                continue
            
            if "energy_now" in bat and "energy_full" in bat:
                total_now += bat["energy_now"]
                total_full += bat["energy_full"]

            if bat["status"] in ["Full", "Charging"]:
                charging = True
        
        if total_full == 0:
            return 0, charging
    
        return total_now * 100 // total_full, charging


    def is_battery_present(self) -> bool:
        "Check the battery presence"

        for i in BAT_PATH.iterdir():
            with open(i / "type") as f:
                if f.read().strip() == "Battery":
                    return True
        return False

    def update_bats(self) -> list:
        "Get status of batteries"

        bats = []
        
        for i in BAT_PATH.iterdir():
            with open(i / "type") as f:
                if f.read().strip() == "Battery":

                    bat = {"name": str(i.name)}

                    with open(i / "capacity") as f:
                        bat["percentage"] = int(f.read().strip())

                    if (i / "model_name").exists():
                        with open(i / "model_name") as f:
                            bat["model_name"] = f.read().strip()
                    else:
                        bat["model_name"] = "Unknown battery"

                    if (i / "scope").exists():
                        with open(i / "scope") as f:
                            bat["scope"] = f.read().strip()
                    else:
                        bat["scope"] = "System"

                    if (i / "status").exists():
                        with open(i / "status") as f:
                            bat["status"] = f.read().strip()
                    else:
                        bat["status"] = "Unknown"


                    if (i / "energy_now").exists() and (i / "energy_full").exists():
                        with open(i / "energy_now") as f:
                            bat["energy_now"] = int(f.read().strip())
                        with open(i / "energy_full") as f:
                            bat["energy_full"] = int(f.read().strip())

                    elif (i / "charge_now").exists() and (i / "charge_full").exists():
                        with open(i / "charge_now") as f:
                            bat["energy_now"] = int(f.read().strip())
                        with open(i / "charge_full") as f:
                            bat["energy_full"] = int(f.read().strip())

                    bats.append(bat)
        return bats
