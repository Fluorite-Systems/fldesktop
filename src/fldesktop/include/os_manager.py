from PySide6.QtWidgets import QApplication
import os
import sys
import logging
import subprocess

class OSManager:
    def __init__(self, comm):
        self.comm = comm

        self.comm.register(
            "osmgr", {
                "get_path": self.get_path,
                "poweroff": self.os_poweroff,
                "reboot": self.os_reboot,
                "suspend": self.os_suspend,
                "logout": self.logout,
                "crash": self.crash
            }
        )
    
    def get_path(self, postfix) -> str | None:
        "Get data path (useful for testing)"

        prefixes = [
            "/system/",
            "/usr/lib/python3/dist-packages/fldesktop/",
            "/",
            "/home/",
            "~/",
            "./",
            "../"
        ] # ^^^^^ Prefixes are sorted like this for security reasons

        for p in prefixes:
            path = p + postfix
            if os.path.exists(path):
                return path
            
        return None

    def os_poweroff(self) -> None:
        "Power off the system"
        self.prepare_logout()
        logging.info("Shutting down via systemctl, goodbye.")
        subprocess.run(["systemctl", "poweroff"])
    
    def os_reboot(self) -> None:
        "Reboot the system"
        self.prepare_logout()
        logging.info("Rebooting via systemctl, goodbye.")
        subprocess.run(["systemctl", "reboot"])
    
    def os_suspend(self) -> None:
        "Show lockscreen and suspend the system"
        self.comm.send("lockscreen", "show")
        subprocess.run(["systemctl", "suspend"])
    
    def logout(self) -> None:
        "Log out"
        self.prepare_logout()
        logging.info("Logging out, goodbye.")
        QApplication.instance().quit()
    
    def prepare_logout(self) -> None:
        "Prepare for logout"
        self.comm.send("fade_effect", "fadeout")
        self.comm.send("pkgmgr", "killall")
        self.comm.send("appserver", "stop")
        self.comm.send("pkgmgr", "unmount")
    
    def crash(self) -> None:
        "Something in fldesktop went really wrong"
        logging.info("Crashing...")
        os._exit(1)
