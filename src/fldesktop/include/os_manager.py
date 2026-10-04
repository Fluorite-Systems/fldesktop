from PySide6.QtCore import QObject, QSocketNotifier

import os
import time
import signal
import socket
import logging
import subprocess


class SignalHandler(QObject):
    def __init__(self, callback, parent=None):
        super().__init__(parent)
        self._callback = callback
        self._handled = False

        self._rsock, self._wsock = socket.socketpair()

        self._rsock.setblocking(False)
        self._wsock.setblocking(False)

        signal.set_wakeup_fd(self._wsock.fileno())

        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda signum, frame: None)

        self._notifier = QSocketNotifier(self._rsock.fileno(), QSocketNotifier.Read, self)
        self._notifier.activated.connect(self._on_activated)

    def _on_activated(self):
        if self._handled:
            return
        self._handled = True

        self._notifier.setEnabled(False)

        signal.set_wakeup_fd(-1)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        try:
            self._rsock.recv(1024)
        except (BlockingIOError, OSError):
            pass

        self._callback()


class OSManager:
    def __init__(self, comm):
        self.comm = comm

        self.comm.register(
            "osmgr", {
                "get_path": self.get_path,
                "poweroff": self.os_poweroff,
                "reboot": self.os_reboot,
                "suspend": self.os_suspend,
                "logout": self.logout
            }
        )

        if not "XDG_RUNTIME_DIR" in os.environ:
            logging.fatal("XDG_RUNTIME_DIR is not specified!")
            self.comm.request("init", "failure")

        self.swatcher = SignalHandler(self.logout)
    
    def get_path(self, postfix) -> str | None:
        "Get data path (useful for testing)"

        prefixes = [
            "/usr/lib/python3/dist-packages/fldesktop/",
            "/",
            "/home/",
            "~/",
            "./",
            "../",
            "/tmp/"
        ] # ^^^^^ Prefixes are sorted like this for security reasons

        for p in prefixes:
            path = p + postfix
            if os.path.exists(path):
                return path
            
        return None

    def os_poweroff(self) -> None:
        "Power off the system"
        logging.info("Shutting down...")
        self.comm.request("ssmgr", "show_shutdown")
        subprocess.Popen(["systemctl", "poweroff", "--no-wall"])
    
    def os_reboot(self) -> None:
        "Reboot the system"
        logging.info("Rebooting...")
        self.comm.request("ssmgr", "show_shutdown", reboot=True)
        subprocess.Popen(["systemctl", "reboot", "--no-wall"])
    
    def os_suspend(self) -> None:
        "Show lockscreen and suspend the system"
        self.comm.request("lockscreen", "show")
        subprocess.run(["systemctl", "suspend"])
    
    def logout(self) -> None:
        "Log out"
        self.comm.request("init", "cleanup")