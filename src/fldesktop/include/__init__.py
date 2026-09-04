from PySide6.QtWidgets import QApplication

import subprocess
import logging


class QApp:
    def __init__(self, _):
        self.app = QApplication()

    def srv_cleanup(self):
        QApplication.instance().exit()

    def exec(self):
        QApplication.instance().exec()
        

class PostInit:
    def __init__(self, comm):
        self.comm = comm

        self.comm.request("lockscreen", "show")
        self.comm.request("fade_effect", "fadein")

    def srv_cleanup(self):
        self.comm.request("fade_effect", "fadeout")


class UserServiceStarter:
    def __init__(self, comm):
        self.comm = comm

        self.start_pipewire()

    def start_pipewire(self):
        
        result = subprocess.run(
            ["systemctl", "--user", "is-active", "pipewire.socket"],
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip() == "active":
            logging.info("PipeWire is already running")
            return

        logging.info("Starting PipeWire")

        subprocess.run(
            ["systemctl", "--user", "enable", "--now",
             "pipewire.socket", "wireplumber.service"],
            capture_output=True,
            text=True,
            check=True
        )
