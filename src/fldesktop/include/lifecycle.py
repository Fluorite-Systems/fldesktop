import logging
import os
import time
import glob
import subprocess


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

        os.environ["XDG_RUNTIME_DIR"] = "/run/user/0/"
        os.makedirs(os.environ["XDG_RUNTIME_DIR"], exist_ok=True)
        os.chmod(os.environ["XDG_RUNTIME_DIR"], 0o700)
        os.chown(os.environ["XDG_RUNTIME_DIR"], 0, 0)

        self.configure_rendering()

        self.comm.request("extsvinit", "run_service", "weston")

    def wait_udev(self):

        if self.is_dev_environment:
            return

        self.comm.request("extsvinit", "run_service", "udev")

        while True:

            cards = glob.glob("/dev/dri/card*")
            events = glob.glob("/dev/input/event*")

            logging.debug(
                (
                    f"Waiting for udev. "
                    f"Cards: {bool(cards)}, "
                    f"events: {bool(events)}"
                )
            )

            if bool(cards) and bool(events):
                break

            time.sleep(0.1)

    def configure_rendering():

        egl_ok = False
        
        try:
            result = subprocess.run(
                ["eglinfo", "-B"], 
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                output = result.stdout.lower()
                egl_ok = not (
                    "llvmpipe" in output
                    or "softpipe" in output
                    or "virgl" in output
                )
        except Exception as e:
            logging.warning(f"Failed to check eglinfo: {e}")

        if egl_ok:
            logging.info("Using Wayland/EGL")
            os.environ["QT_QPA_PLATFORM"] = "wayland"
            os.environ["PYOPENGL_PLATFORM"] = "egl"
            os.environ["WAYLAND_DISPLAY"] = "wayland-0"
        else:
            logging.info("Using XCB/GLX")
            os.environ["QT_QPA_PLATFORM"] = "xcb"
            os.environ["PYOPENGL_PLATFORM"] = "glx"
            os.environ["DISPLAY"] = ":0"

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