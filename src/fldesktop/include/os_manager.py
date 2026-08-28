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
                "logout": self.logout
            }
        )

        if not "XDG_RUNTIME_DIR" in os.environ:
            logging.fatal("XDG_RUNTIME_DIR is not specified!")
            self.comm.request("init", "failure")
    
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
        subprocess.Popen(["systemctl", "poweroff", "--no-block", "--no-wall"])
        sys.exit(0)
    
    def os_reboot(self) -> None:
        "Reboot the system"
        self.prepare_logout()
        logging.info("Rebooting via systemctl, goodbye.")
        subprocess.Popen(["systemctl", "reboot", "--no-block", "--no-wall"])
        sys.exit(0)
    
    def os_suspend(self) -> None:
        "Show lockscreen and suspend the system"
        self.comm.request("lockscreen", "show")
        subprocess.run(["systemctl", "suspend"])
    
    def logout(self) -> None:
        "Log out"

        self.comm.request("init", "cleanup")
        #self.prepare_logout()
        #logging.info("Logging out, goodbye.")
        #QApplication.instance().quit()
    
    def prepare_logout(self) -> None:
        "Prepare for logout"
        self.comm.request("fade_effect", "fadeout")
        self.comm.request("pkgmgr", "killall")
        self.comm.request("appserver", "stop")
        self.comm.request("pkgmgr", "unmount") 
