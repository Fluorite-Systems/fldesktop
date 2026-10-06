import logging
import os
import time
import glob


class LifeCycle:
    def __init__(self, comm):

        self.comm = comm
        self.comm.register(
            "lifecycle", {
                "shutdown": self.shutdown,
                "reboot": self.reboot,
                "logout": self.logout,
                "is_dev_environment": self.get_is_dev_env
            }
        )

        self.comm.subscribe("startupscreen_shown", self.start_services)
        self.comm.subscribe("shutdownscreen_shown", self.stop_services)

        self.is_dev_environment = any(
            os.path.exists(p) for p in (
                "/run/systemd/system",
                "/run/runit",
                "/run/openrc"
            )
        )

        self.wait_udev()
        self.setup_env()

    def setup_env(self):

        if self.is_dev_environment:
            return

        os.environ["XDG_RUNTIME_DIR"] = "/run/user/1000/"
        os.makedirs(os.environ["XDG_RUNTIME_DIR"], exist_ok=True)

        self.comm.request("extsvinit", "run_service", "seatd")
        self.comm.request("extsvinit", "run_service", "cage")

    def wait_udev(self):

        if self.is_dev_environment:
            return

        self.comm.request("extsvinit", "run_service", "udev")

        while True:

            cards = glob.glob("/dev/dri/card*")
            renders = glob.glob("/dev/dri/renderD*")
            events = glob.glob("/dev/input/event*")

            logging.debug(
                (
                    f"Waiting for udev. "
                    f"Cards: {bool(cards)}, "
                    f"renders: {bool(renders)}, "
                    f"events: {bool(renders)}"
                )
            )

            if bool(cards) and bool(renders) and bool(events):
                break

            time.sleep(0.1)

    def start_services(self):

        if self.is_dev_environment:
            return

        self.comm.request("extsvinit", "full_init")

    def stop_services(self):

        self.comm.request("extsvinit", "shutdown")

    def shutdown(self):

        self.comm.request("startupscreen", "show_shutdown")

    def reboot(self):

        self.comm.request("startupscreen", "show_shutdown")

    def logout(self):

        self.stop_services()
        self.comm.request("init", "cleanup")

    def get_is_dev_env(self):
        return self.is_dev_environment